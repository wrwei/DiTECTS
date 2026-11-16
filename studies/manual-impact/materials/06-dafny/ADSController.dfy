// Auto-generated Dafny verification code from Java source
// Source: ADSController.java (Spoon EMF model)
//
// Hand-strengthened with domain safety properties (beyond the generated defaults):
//   REQ-ADS-002 (Valid invariant): the duty-bed selector names BedA or BedB.
//     Physical bed availability and detritiation are outside this model.
//   REQ-ADS-007 (transition/step postconditions): a PowerLoss event drives
//     the controller to FailSafe from ANY operating mode.
//   REQ-ADS-006 (transition/step postconditions): completing a changeover
//     hands duty to the other bed, so the two beds alternate.

datatype Mode = NormalOperation | Changeover | FailSafe

datatype Dryer = BedA | BedB
datatype InputEvent = NoEvent | PowerLoss | DewpointHigh | ChangeoverComplete | BackupRestored

// Complete mode/event table. Unused inputs leave the mode unchanged.
function nextMode(m: Mode, e: InputEvent): Mode
{
    match m
    case NormalOperation =>
        if e == PowerLoss then FailSafe else if e == DewpointHigh then Changeover else NormalOperation
    case Changeover =>
        if e == PowerLoss then FailSafe else if e == ChangeoverComplete then NormalOperation else Changeover
    case FailSafe =>
        if e == BackupRestored then NormalOperation else FailSafe
}

// REQ-ADS-006: the standby bed becomes active when changeover completes, so the beds alternate.
function nextDryer(d: Dryer): Dryer
{
    if d == BedA then BedB else BedA
}

lemma NextDryerSwitchesBed(d: Dryer)
    ensures nextDryer(d) != d
{
}

class ADSController {
    var mode: Mode

    // The controller changes duty bed only when a changeover completes.
    var activeDryer: Dryer

    // REQ-ADS-002 abstraction: a valid bed selector, without physical bed state.
    ghost predicate Valid()
        reads this
    {
        activeDryer == BedA || activeDryer == BedB
    }

    constructor()
        ensures mode == NormalOperation
        ensures Valid()
    {
        mode := NormalOperation;
        activeDryer := BedA;
    }

    method transitionFromNormalOperation(event: InputEvent)
        requires mode == NormalOperation
        requires Valid()
        modifies this
        ensures Valid()
        ensures event == PowerLoss ==> mode == FailSafe   // REQ-ADS-007
        ensures mode == nextMode(old(mode), event)
        ensures activeDryer == old(activeDryer)
    {
        if (event == PowerLoss) {
            mode := FailSafe;
            // action: EnterFailSafe
        }
        else if (event == DewpointHigh) {
            mode := Changeover;
            // action: RaiseAlarm
        }
    }

    method transitionFromChangeover(event: InputEvent)
        requires mode == Changeover
        requires Valid()
        modifies this
        ensures Valid()
        ensures event == ChangeoverComplete ==> activeDryer == nextDryer(old(activeDryer))   // REQ-ADS-006
        ensures event != ChangeoverComplete ==> activeDryer == old(activeDryer)
        ensures event == PowerLoss ==> mode == FailSafe   // REQ-ADS-007
        ensures mode == nextMode(old(mode), event)
    {
        if (event == PowerLoss) {
            mode := FailSafe;
            // action: EnterFailSafe
        }
        else if (event == ChangeoverComplete) {
            activeDryer := nextDryer(activeDryer);
            mode := NormalOperation;
        }
    }

    method transitionFromFailSafe(event: InputEvent)
        requires mode == FailSafe
        requires Valid()
        modifies this
        ensures Valid()
        ensures event == PowerLoss ==> mode == FailSafe   // REQ-ADS-007 (already FailSafe; stays)
        ensures mode == nextMode(old(mode), event)
        ensures activeDryer == old(activeDryer)
    {
        if (event == BackupRestored) {
            mode := NormalOperation;
            // action: RestoreNormal
        }
    }

    method step(event: InputEvent)
        requires Valid()
        modifies this
        ensures Valid()
        ensures old(mode) == Changeover && event == ChangeoverComplete ==> activeDryer == nextDryer(old(activeDryer))   // REQ-ADS-006
        ensures event == PowerLoss ==> mode == FailSafe   // REQ-ADS-007 (from any mode)
        ensures mode == nextMode(old(mode), event)
        ensures !(old(mode) == Changeover && event == ChangeoverComplete) ==> activeDryer == old(activeDryer)
    {
        if (mode == NormalOperation) {
            transitionFromNormalOperation(event);
        }
        else if (mode == Changeover) {
            transitionFromChangeover(event);
        }
        else if (mode == FailSafe) {
            transitionFromFailSafe(event);
        }
    }
}
