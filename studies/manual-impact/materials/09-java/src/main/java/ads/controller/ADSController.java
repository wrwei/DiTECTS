package ads.controller;

import ads.actuator.Actuator;
import ads.datamodel.Dryer;
import ads.event.InputEvent;
import ads.event.OutputEvent;
import ads.mode.ADSMode;
import ads.sensor.DryerFunctions;

/**
 * Atmosphere Detritiation System (ADS) supervisory controller — the
 * software realisation of the {@code ADSOperation} state machine in the
 * SysML design model ({@code 02-design.sysml}).
 *
 * <p>Single-method, mode-nested if-else state machine over
 * {@link ADSMode}. {@code NormalOperation} is the initial mode; there is
 * no terminal state (the ADS is always-on). Loss of off-site power is the
 * highest-priority transition and is duplicated in every applicable mode
 * block, so the plant is driven to {@code FailSafe} from anywhere
 * (REQ-ADS-007). A dewpoint alarm requests changeover; completion selects
 * the other bed (REQ-ADS-002, REQ-ADS-006). Physical bed availability and
 * detritiation are outside this controller model.</p>
 */
public final class ADSController {

    private ADSMode currentMode = ADSMode.NormalOperation;
    private final DryerFunctions dryers;
    private final Actuator actuator;

    private Dryer activeDryer = Dryer.BedA;

    public ADSController(DryerFunctions dryers, Actuator actuator) {
        this.dryers = dryers;
        this.actuator = actuator;
    }

    public ADSMode currentMode() {
        return currentMode;
    }

    public Dryer activeDryer() {
        return activeDryer;
    }

    public void step(InputEvent event) {
        if (currentMode == ADSMode.NormalOperation) {
            if (event instanceof InputEvent.PowerLoss) {
                actuator.apply(new OutputEvent.EnterFailSafe());
                currentMode = ADSMode.FailSafe;
            } else if (event instanceof InputEvent.DewpointHigh) {
                actuator.apply(new OutputEvent.RaiseAlarm());
                actuator.apply(new OutputEvent.StartChangeover());
                currentMode = ADSMode.Changeover;
            }
        } else if (currentMode == ADSMode.Changeover) {
            if (event instanceof InputEvent.PowerLoss) {
                actuator.apply(new OutputEvent.EnterFailSafe());
                currentMode = ADSMode.FailSafe;
            } else if (event instanceof InputEvent.ChangeoverComplete) {
                activeDryer = dryers.nextDryer(activeDryer);
                currentMode = ADSMode.NormalOperation;
            }
        } else if (currentMode == ADSMode.FailSafe) {
            if (event instanceof InputEvent.BackupRestored) {
                actuator.apply(new OutputEvent.RestoreNormal());
                currentMode = ADSMode.NormalOperation;
            }
        }
    }
}
