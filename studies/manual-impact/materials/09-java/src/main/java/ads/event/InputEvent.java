package ads.event;

/**
 * Boundary events consumed (as transition triggers) by the ADS
 * supervisory state machine. Each corresponds to an {@code accept}
 * trigger on the {@code ADSOperation} state machine in the SysML design
 * model ({@code 02-design.sysml}).
 *
 * <ul>
 *   <li>{@code DewpointHigh} — outlet dewpoint has crossed the alarm
 *       threshold, requesting a bed changeover (REQ-ADS-003, REQ-ADS-006).</li>
 *   <li>{@code ChangeoverComplete} — the standby bed is online and the
 *       changeover sequence has finished (REQ-ADS-002).</li>
 *   <li>{@code PowerLoss} — loss of off-site power; highest-priority
 *       safety override (REQ-ADS-007).</li>
 *   <li>{@code BackupRestored} — the backup supply is available, allowing
 *       a return to normal operation (REQ-ADS-007).</li>
 * </ul>
 */
public sealed interface InputEvent {

    /** dewpointHigh — outlet dewpoint above the alarm threshold. */
    record DewpointHigh() implements InputEvent {
    }

    /** changeoverComplete — standby bed online, changeover finished. */
    record ChangeoverComplete() implements InputEvent {
    }

    /** powerLoss — loss of off-site power. */
    record PowerLoss() implements InputEvent {
    }

    /** backupRestored — backup supply available. */
    record BackupRestored() implements InputEvent {
    }
}
