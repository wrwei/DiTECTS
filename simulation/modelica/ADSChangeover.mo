/*  ===========================================================================
 *  ADSChangeover - atmosphere-detritiation dual-bed changeover transient
 *  ===========================================================================
 *
 *  WHAT THIS MODEL IS
 *  ------------------
 *  A minimal hybrid model of the ADS (Atmosphere Detritiation System)
 *  molecular-sieve dryer as it cycles between its two adsorber beds. The ADS
 *  removes tritiated water vapour from a glovebox / room atmosphere; its
 *  effectiveness is measured by the DECONTAMINATION FACTOR (DF) - the ratio of
 *  inlet to outlet tritium concentration. A higher DF means a drier, cleaner
 *  outlet (DF = 1000 means the outlet holds 1/1000 of the inlet activity). The
 *  plant must keep DF at or above an authorised target AT ALL TIMES, including
 *  during the brief changeover when the saturated duty bed is taken offline for
 *  regeneration and the fresh standby bed is brought online.
 *
 *  WHY IT EXISTS (the safety claim)
 *  --------------------------------
 *  This model is the executable evidence behind GSN Goal G3 / Solution Sn2 of
 *  the ADS safety case (../../04-gsn-safety-case.md): "bed changeover preserves
 *  the detritiation function". It speaks to REQ-ADS-001 (DF >= 1000),
 *  REQ-ADS-002 (continuity of detritiation) and REQ-ADS-006 (dual-bed
 *  redundancy). The terminal `assert` turns that claim into a machine-checkable
 *  property: a completed simulation supports the DF assertion over that run.
 *  It does not prove that the controller or physical plant will behave so.
 *
 *  HOW IT WORKS (the physics, simplified)
 *  --------------------------------------
 *  A molecular-sieve bed adsorbs moisture until it saturates, so its DF decays
 *  over time. We model that decay as a first-order (exponential) process: a
 *  fresh bed starts at DFfresh and decays with time constant tSat.
 *  This algebraic periodic trajectory assumes bed swaps on a fixed period
 *  tCycle, so the EFFECTIVE plant DF is always the DF of a bed that is at most
 *  tCycle seconds old. The variable `phase = mod(time, tCycle)` is the age of
 *  the currently-active bed; it ramps up then snaps back to 0 at every
 *  changeover, which is what draws the saw-tooth. Because tCycle is shorter
 *  than tSat*ln(DFfresh/DFtarget), the worst-case DF - at the very end of a
 *  cycle, just before the swap - still exceeds DFtarget, so continuity holds
 *  with margin.
 *
 *  WHAT TO DO WITH IT
 *  ------------------
 *  Simulate over 0..20000 s (about three cycles) and plot DF: it saw-tooths
 *  between DFfresh just after each swap and DFfresh*exp(-tCycle/tSat) ~ 1390
 *  just before each swap, and every tooth bottom sits above DFtarget = 1000.
 *  Run it in OpenModelica (omc / OMEdit).
 *
 *  NOTE ON FIDELITY
 *  ----------------
 *  Values are realistic illustrations for the worked example, not licensed-plant
 *  data. The model abstracts a real two-bed adsorption dryer down to the single
 *  property the safety argument cares about (outlet DF versus time through a
 *  swap). It is deliberately the simplest thing that makes the continuity claim
 *  executable. It assumes instantaneous swaps and a freshly regenerated bed
 *  at each swap; it does not model valve delays, regeneration or backup power.
 *  =========================================================================== */
model ADSChangeover
  "ADS dual-bed changeover transient: plant DF stays above the authorised target through every bed swap (GSN Sn2 / Goal G3; REQ-ADS-001/002/006)"

  // ---- Parameters ----------------------------------------------------------

  // DFtarget: the authorised MINIMUM decontamination factor the plant must
  //   never fall below (REQ-ADS-001). This is the safety limit the whole model
  //   exists to demonstrate compliance with - the assert at the bottom checks
  //   DF >= DFtarget. DF = 1000 means the outlet tritium concentration is
  //   1/1000 of the inlet. Dimensionless.
  parameter Real DFtarget = 1000.0 "Authorised minimum decontamination factor (REQ-ADS-001) [-]";

  // DFfresh: the decontamination factor of a freshly regenerated bed at the
  //   instant it comes online (phase = 0). This is the best the dryer achieves;
  //   DF decays away from here as the bed loads with moisture. It sets the TOP
  //   of the saw-tooth. Dimensionless.
  parameter Real DFfresh = 8000.0 "Decontamination factor of a freshly regenerated bed [-]";

  // tSat: the bed SATURATION time constant. It governs how fast DF decays as
  //   the sieve fills with water - DF(t) = DFfresh*exp(-t/tSat) - so after one
  //   tSat the DF has fallen to ~37% (1/e) of DFfresh. A larger tSat means
  //   slower saturation, i.e. the bed stays effective for longer. Seconds.
  parameter Real tSat = 4000.0 "Bed saturation time constant [s]";

  // tCycle: the CHANGEOVER period - how long a bed serves as the duty bed
  //   before the controller swaps to the fresh standby and sends the saturated
  //   one to regeneration. This is the design knob that guarantees continuity:
  //   it must be short enough that the bed's DF has not decayed below DFtarget
  //   by the end of a cycle, i.e. tCycle < tSat*ln(DFfresh/DFtarget) =
  //   4000*ln(8) ~ 8317 s. The chosen 7000 s leaves a comfortable margin
  //   (worst-case DF ~ 1390 vs the 1000 limit). Seconds.
  parameter Real tCycle = 7000.0 "Changeover period: the duty bed is swapped to the fresh standby every tCycle [s]";

  // ---- Variables -----------------------------------------------------------

  // phase: the AGE of the currently-active duty bed - the time elapsed since it
  //   last came online. It resets to 0 at every changeover (each tCycle), which
  //   is exactly what produces the saw-tooth. Algebraic (computed from time),
  //   not an integrated state. Seconds.
  Real phase "Time since the active duty bed came online [s]";

  // DF: the plant DECONTAMINATION FACTOR presented at the dryer outlet. This is
  //   the model's headline output and the quantity the safety property
  //   constrains; it tracks the active bed's DF, which decays with `phase`.
  //   Dimensionless.
  Real DF "Plant decontamination factor presented at the outlet [-]";

equation
  // phase = age of the active bed within the current changeover cycle. mod()
  // wraps the simulation time into [0, tCycle): it ramps 0 -> tCycle then snaps
  // back to 0 at each swap, encoding "the duty bed is at most tCycle s old".
  phase = mod(time, tCycle);

  // First-order (exponential) decay of decontamination factor as the active bed
  // adsorbs moisture: a fresh bed (phase = 0) gives DFfresh and then falls with
  // time constant tSat. The swap (phase resetting to 0) restores DF to DFfresh,
  // giving the saw-tooth. The cycle MINIMUM is DFfresh*exp(-tCycle/tSat) =
  // 8000*exp(-7000/4000) = 8000*exp(-1.75) ~ 1390, which stays above the
  // DFtarget = 1000 limit by construction.
  DF = DFfresh * exp(-phase / tSat);

  // Executable continuity property (REQ-ADS-001 / REQ-ADS-002): the simulation
  // is allowed to complete only if the plant DF never breaches the authorised
  // target. If DF ever dips below DFtarget the assert fires and the run fails,
  // so a clean run supports continuity over this experiment, under the
  // model's assumptions about switching and regenerated beds.
  assert(DF >= DFtarget, "Detritiation continuity violated: plant DF fell below the authorised target during changeover");

  // Default experiment: 0..20000 s (about three changeover cycles) sampled
  // every 10 s. Plot DF to see the saw-tooth staying above DFtarget.
  annotation(experiment(StartTime = 0, StopTime = 20000, Interval = 10));
end ADSChangeover;
