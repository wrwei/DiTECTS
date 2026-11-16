package ads.datamodel;

/**
 * The two independent molecular-sieve dryer beds (REQ-ADS-006). Exactly
 * one bed is active at any time; changeover swaps the active bed for the
 * standby bed. Modelled as a controller state variable so the formal
 * model can reason that the detritiation function is never lost
 * (REQ-ADS-002).
 */
public enum Dryer {
    BedA,
    BedB
}
