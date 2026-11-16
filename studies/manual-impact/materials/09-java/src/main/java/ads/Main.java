package ads;

import ads.actuator.Actuator;
import ads.controller.ADSController;
import ads.event.InputEvent;
import ads.sensor.DryerFunctions;

/**
 * Tiny driver that steps the {@link ADSController} through the changeover /
 * fail-safe choreography of the {@code ADSOperation} state machine — the same
 * sequence the digital twin animates. Lets {@code gradle run} demonstrate the
 * controller; the controller itself is a library with no entry point.
 */
public final class Main {

    public static void main(String[] args) {
        Actuator actuator = new Actuator();
        ADSController controller = new ADSController(new DryerFunctions(), actuator);

        System.out.println("ADS controller demo — stepping the ADSOperation state machine");
        report(controller, "start");

        controller.step(new InputEvent.DewpointHigh());       // dewpoint alarm → changeover
        report(controller, "dewpointHigh");
        controller.step(new InputEvent.ChangeoverComplete()); // standby online → bed swaps
        report(controller, "changeoverComplete");
        controller.step(new InputEvent.PowerLoss());          // loss of power → fail-safe
        report(controller, "powerLoss");
        controller.step(new InputEvent.BackupRestored());     // backup up → normal
        report(controller, "backupRestored");

        System.out.println("Done.");
    }

    private static void report(ADSController c, String event) {
        System.out.printf("  after %-20s mode=%-15s activeDryer=%s%n",
            event, c.currentMode(), c.activeDryer());
    }
}
