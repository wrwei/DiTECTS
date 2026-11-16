package ads.sensor;

import ads.annotation.SensorService;
import ads.datamodel.Dryer;

/**
 * Pure domain functions over the dryer-bed configuration. Referenced from
 * the controller's changeover action, so the M2M lifts {@code nextDryer}
 * into a RoboChart {@code function} declaration.
 */
@SensorService
public final class DryerFunctions {

    /**
     * nextDryer(current) : Dryer — the standby bed that becomes active once
     * changeover completes. The selector alternates between its two values
     * (REQ-ADS-002, REQ-ADS-006). This does not establish bed availability or
     * successful regeneration.
     */
    public Dryer nextDryer(Dryer current) {
        if (current == Dryer.BedA) {
            return Dryer.BedB;
        }
        return Dryer.BedA;
    }
}
