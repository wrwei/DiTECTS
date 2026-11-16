package ads.mode;

/**
 * Operating modes of the Atmosphere Detritiation System supervisory state
 * machine, mirroring the {@code ADSOperation} state machine in the SysML
 * design model ({@code 02-design.sysml}). The controller is always-on:
 * there is no terminal (Final) state.
 *
 * <ul>
 *   <li>{@code NormalOperation} — detritiation running on the active dryer bed.</li>
 *   <li>{@code Changeover} — switching to the standby bed on a dewpoint alarm
 *       (REQ-ADS-006), detritiation function preserved throughout (REQ-ADS-002).</li>
 *   <li>{@code FailSafe} — entered on loss of off-site power; recovers on the
 *       backup supply (REQ-ADS-007).</li>
 * </ul>
 */
public enum ADSMode {
    NormalOperation,
    Changeover,
    FailSafe
}
