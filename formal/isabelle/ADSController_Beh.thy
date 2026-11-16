theory ADSController_Beh
imports "Z_Machines.Z_Machine"
begin

subsection \<open> Introduction \<close>

text \<open> This theory file is to model the ADSController state machine in Z Machine notations.\<close>

notation undefined ("???")

subsection \<open> type definition \<close>

datatype ('s, 'e) tag =
  State (ofState: 's) | Event (ofEvent: 'e)

abbreviation "is_Event x \<equiv> \<not> is_State x"

type_synonym ('s, 'e) rctrace = "('s, 'e) tag list"

definition wf_rcstore :: "('s, 'e) rctrace \<Rightarrow> 's \<Rightarrow> 's option \<Rightarrow> bool" where
[z_defs]: "wf_rcstore tr st final = (
     length(tr) > 0 
   \<and> tr ! ((length tr) -1) = State st 
   \<and> (final \<noteq> None \<longrightarrow> (\<forall>i<length tr. tr ! i = State (the final) \<longrightarrow> i= (length tr) -1)) 
   \<and> (filter is_State tr) ! (length (filter is_State tr) -1) = State  st)"
   
enumtype St = NormalOperation | Changeover | FailSafe | initial 
 


enumtype Evt = powerLoss | enterFailSafe | dewpointHigh | raiseAlarm | startChangeover | changeoverComplete | backupRestored | restoreNormal 
 


enumtype Dryer = BedA | BedB

instantiation real :: default
begin
  definition default_real :: "real" where "default_real = 0"
  instance ..
end

instantiation real :: "show"
begin
  instance ..
end

text \<open> function definition \<close>

(* REQ-ADS-006: when changeover completes, the standby bed becomes the active bed. *)
definition nextDryer :: "Dryer \<Rightarrow> Dryer" where
  [z_defs]: "nextDryer d = (if d = BedA then BedB else BedA)"

lemma nextDryer_switches_bed: "nextDryer d \<noteq> d"
  by (auto simp add: nextDryer_def)

subsection \<open> State Space \<close>

zstore ADSController =
  activeDryer :: "Dryer"
  st::"St"
  tr :: "(St, Evt) tag list"
  triggers:: "Evt set"
  where inv:
    "wf_rcstore tr st None"

subsection \<open> Operations \<close>

zoperation InitialToNormalOperation =
  over ADSController
  pre "st= initial"
  update "[st\<Zprime>= NormalOperation
         ,tr\<Zprime> =tr  @ [State NormalOperation]
         ,triggers\<Zprime> = {powerLoss, dewpointHigh}
         ]"
        
zoperation NormalOperationToFailSafe =
  over ADSController
  pre "st= NormalOperation"
  update "[st\<Zprime>= FailSafe
         ,tr\<Zprime> =tr @ [Event powerLoss]@ [Event enterFailSafe] @ [State FailSafe]
         ,triggers\<Zprime> = {backupRestored}
         ]"
        
zoperation NormalOperationToChangeover =
  over ADSController
  pre "st= NormalOperation"
  update "[st\<Zprime>= Changeover
         ,tr\<Zprime> =tr @ [Event dewpointHigh]@ [Event raiseAlarm]@ [Event startChangeover] @ [State Changeover]
         ,triggers\<Zprime> = {powerLoss, changeoverComplete}
         ]"
        
zoperation ChangeoverToFailSafe =
  over ADSController
  pre "st= Changeover"
  update "[st\<Zprime>= FailSafe
         ,tr\<Zprime> =tr @ [Event powerLoss]@ [Event enterFailSafe] @ [State FailSafe]
         ,triggers\<Zprime> = {backupRestored}
         ]"
        
zoperation ChangeoverToNormalOperation =
  over ADSController
  pre "st= Changeover"
  update "[st\<Zprime>= NormalOperation
         ,tr\<Zprime> =tr @ [Event changeoverComplete] @ [State NormalOperation]
         ,triggers\<Zprime> = {powerLoss, dewpointHigh}
         ,activeDryer\<Zprime> = nextDryer activeDryer
         ]"
        
zoperation FailSafeToNormalOperation =
  over ADSController
  pre "st= FailSafe"
  update "[st\<Zprime>= NormalOperation
         ,tr\<Zprime> =tr @ [Event backupRestored]@ [Event restoreNormal] @ [State NormalOperation]
         ,triggers\<Zprime> = {powerLoss, dewpointHigh}
         ]"
        

  
definition Init :: "ADSController subst" where
  [z_defs]:
  "Init =
  [activeDryer\<leadsto> BedA
  ,st\<leadsto> initial
  ,tr\<leadsto> [State initial]
  ,triggers\<leadsto> {}
  ]"
  
  
(* Keep the event vocabulary separate from the executable operation list. *)
chantype ADSControllerMachine_chan =
  initialToNormalOperation :: unit
  normalOperationToFailSafe :: unit
  normalOperationToChangeover :: unit
  changeoverToFailSafe :: unit
  changeoverToNormalOperation :: unit
  failSafeToNormalOperation :: unit
  initialToNormalOperation_Out :: unit
  normalOperationToFailSafe_Out :: unit
  normalOperationToChangeover_Out :: unit
  changeoverToFailSafe_Out :: unit
  changeoverToNormalOperation_Out :: unit
  failSafeToNormalOperation_Out :: unit

setup \<open>Z_Machine.mk_chan_show_inst "ADSControllerMachine_chan"
  ["InitialToNormalOperation", "NormalOperationToFailSafe", "NormalOperationToChangeover", "ChangeoverToFailSafe", "ChangeoverToNormalOperation", "FailSafeToNormalOperation"]\<close>

definition ADSController_operations :: "(ADSControllerMachine_chan, ADSController) htree list" where
  "ADSController_operations = [
    zop_event initialToNormalOperation InitialToNormalOperation_type InitialToNormalOperation_pre initialToNormalOperation_Out InitialToNormalOperation,
    zop_event normalOperationToFailSafe NormalOperationToFailSafe_type NormalOperationToFailSafe_pre normalOperationToFailSafe_Out NormalOperationToFailSafe,
    zop_event normalOperationToChangeover NormalOperationToChangeover_type NormalOperationToChangeover_pre normalOperationToChangeover_Out NormalOperationToChangeover,
    zop_event changeoverToFailSafe ChangeoverToFailSafe_type ChangeoverToFailSafe_pre changeoverToFailSafe_Out ChangeoverToFailSafe,
    zop_event changeoverToNormalOperation ChangeoverToNormalOperation_type ChangeoverToNormalOperation_pre changeoverToNormalOperation_Out ChangeoverToNormalOperation,
    zop_event failSafeToNormalOperation FailSafeToNormalOperation_type FailSafeToNormalOperation_pre failSafeToNormalOperation_Out FailSafeToNormalOperation]"

definition ADSControllerMachine :: "ADSControllerMachine_chan process" where
  "ADSControllerMachine = z_machine Init ADSController_inv ADSController_operations (\<lambda> _. False)"

definition ADSController_step :: "(ADSControllerMachine_chan, ADSController) htree" where
  "ADSController_step = z_machine_main ADSController_operations"

lemma ADSController_step_visible: "is_Vis (ADSController_step s)"
  by (simp add: ADSController_step_def ADSController_operations_def z_machine_main_def
                extchoice_fun_def zop_event_def input_in_where_def inp_in_where_def)

lemma ADSController_machine_body:
  "ADSControllerMachine = process Init (iterate (\<lambda> _. True) ADSController_step)"
  by (simp add: ADSControllerMachine_def z_machine_def ADSController_step_def comp_def)

fun ADSController_input_event :: "ADSControllerMachine_chan \<Rightarrow> Evt option" where
  "ADSController_input_event (normalOperationToFailSafe_C ()) = Some powerLoss" |
  "ADSController_input_event (changeoverToFailSafe_C ()) = Some powerLoss" |
  "ADSController_input_event (normalOperationToChangeover_C ()) = Some dewpointHigh" |
  "ADSController_input_event (changeoverToNormalOperation_C ()) = Some changeoverComplete" |
  "ADSController_input_event (failSafeToNormalOperation_C ()) = Some backupRestored" |
  "ADSController_input_event _ = None"

definition ADSController_inputs :: "ADSController \<Rightarrow> Evt set" where
  "ADSController_inputs s = {e. \<exists> c \<in> pdom (un_Vis (ADSController_step s)).
                                ADSController_input_event c = Some e}"

lemma ADSController_inputs_by_mode:
  "ADSController_inputs s =
    (if lens_get st s = NormalOperation then {powerLoss, dewpointHigh}
     else if lens_get st s = Changeover then {powerLoss, changeoverComplete}
     else if lens_get st s = FailSafe then {backupRestored} else {})"
  by (simp add: ADSController_inputs_def ADSController_step_def ADSController_operations_def z_machine_main_def extchoice_fun_def
                zop_event_def input_in_where_def inp_in_where_def excl_comb_def dom_prism_fun z_defs;
      expr_simp; auto)

(* Every operation the machine offers, by mode: startup only from the initial
   state, and no recovery from FailSafe other than on backup restoration. *)
lemma ADSController_offered_by_mode:
  "pdom (un_Vis (ADSController_step s)) =
    (if lens_get st s = initial then {initialToNormalOperation_C ()}
     else if lens_get st s = NormalOperation then {normalOperationToFailSafe_C (), normalOperationToChangeover_C ()}
     else if lens_get st s = Changeover then {changeoverToFailSafe_C (), changeoverToNormalOperation_C ()}
     else if lens_get st s = FailSafe then {failSafeToNormalOperation_C ()} else {})"
  by (simp add: ADSController_step_def ADSController_operations_def z_machine_main_def extchoice_fun_def
                zop_event_def input_in_where_def inp_in_where_def excl_comb_def dom_prism_fun z_defs;
      expr_simp; auto)

(* Destination expected for each machine event, independent of the operations list. *)
fun ADSController_channel_target :: "ADSControllerMachine_chan \<Rightarrow> St option" where
  "ADSController_channel_target (initialToNormalOperation_C ()) = Some NormalOperation" |
  "ADSController_channel_target (normalOperationToFailSafe_C ()) = Some FailSafe" |
  "ADSController_channel_target (normalOperationToChangeover_C ()) = Some Changeover" |
  "ADSController_channel_target (changeoverToFailSafe_C ()) = Some FailSafe" |
  "ADSController_channel_target (changeoverToNormalOperation_C ()) = Some NormalOperation" |
  "ADSController_channel_target (failSafeToNormalOperation_C ()) = Some NormalOperation" |
  "ADSController_channel_target _ = None"

(* The machine runs, for each offered event, an operation that reaches that
   event's destination: an input cannot be bound to another operation. *)
lemma ADSController_handler_targets:
  "\<lbrakk> c \<in> pdom (un_Vis (ADSController_step s)); s' \<in> retvals (pfun_app (un_Vis (ADSController_step s)) c) \<rbrakk>
   \<Longrightarrow> ADSController_channel_target c = Some (lens_get st s')"
  by (simp add: ADSController_step_def ADSController_operations_def z_machine_main_def extchoice_fun_def zop_event_def input_in_where_def inp_in_where_def excl_comb_def dom_prism_fun output_return_def z_defs; expr_simp; auto simp add: prism_fun_def mk_zop_def seq_itree_def kleisli_comp_def assume_def assigns_def proc_ret_def outp_as_inp retvals_inp_in split: if_splits)

subsection \<open> Structural Invariants \<close>

lemma Init_inv [hoare_lemmas]: "Init establishes ADSController_inv"
  by (zpog_full; auto simp add: wf_rcstore_def nth_append)

lemma InitialToNormalOperation_inv [hoare_lemmas]: "InitialToNormalOperation() preserves ADSController_inv"
  by (zpog_full; auto simp add: wf_rcstore_def nth_append)

lemma NormalOperationToFailSafe_inv [hoare_lemmas]: "NormalOperationToFailSafe() preserves ADSController_inv"
  by (zpog_full; auto simp add: wf_rcstore_def nth_append)

lemma NormalOperationToChangeover_inv [hoare_lemmas]: "NormalOperationToChangeover() preserves ADSController_inv"
  by (zpog_full; auto simp add: wf_rcstore_def nth_append)

lemma ChangeoverToFailSafe_inv [hoare_lemmas]: "ChangeoverToFailSafe() preserves ADSController_inv"
  by (zpog_full; auto simp add: wf_rcstore_def nth_append)

lemma ChangeoverToNormalOperation_inv [hoare_lemmas]: "ChangeoverToNormalOperation() preserves ADSController_inv"
  by (zpog_full; auto simp add: wf_rcstore_def nth_append)

lemma FailSafeToNormalOperation_inv [hoare_lemmas]: "FailSafeToNormalOperation() preserves ADSController_inv"
  by (zpog_full; auto simp add: wf_rcstore_def nth_append)


subsection \<open> Safety Requirements \<close>

(* REQ-ADS-007: a loss of off-site power drives the plant to FailSafe from any
   mode, and FailSafe is stable -- once there, the only accepted trigger is
   backupRestored (the controller cannot wander out of fail-safe on its own). *)
zexpr R1 is "st = FailSafe \<longrightarrow> triggers = {backupRestored}"

lemma  "Init establishes R1"
  by (zpog_full; auto)

lemma "InitialToNormalOperation() preserves R1 under ADSController_inv"
  by (zpog_full; auto)
  
lemma "NormalOperationToFailSafe() preserves R1 under ADSController_inv"
  by (zpog_full; auto)
  
lemma "NormalOperationToChangeover() preserves R1 under ADSController_inv"
  by (zpog_full; auto)
  
lemma "ChangeoverToFailSafe() preserves R1 under ADSController_inv"
  by (zpog_full; auto)
  
lemma "ChangeoverToNormalOperation() preserves R1 under ADSController_inv"
  by (zpog_full; auto)
  
lemma "FailSafeToNormalOperation() preserves R1 under ADSController_inv"
  by (zpog_full; auto)

(* REQ-ADS-002 abstraction: the selector names one of the two beds.
   This does not establish physical bed availability or detritiation. *)
zexpr R2 is "activeDryer = BedA \<or> activeDryer = BedB"

lemma "Init establishes R2"
  by (zpog_full; auto)

lemma "InitialToNormalOperation() preserves R2 under ADSController_inv"
  by (zpog_full; auto)

lemma "NormalOperationToFailSafe() preserves R2 under ADSController_inv"
  by (zpog_full; auto)

lemma "NormalOperationToChangeover() preserves R2 under ADSController_inv"
  by (zpog_full; auto)

lemma "ChangeoverToFailSafe() preserves R2 under ADSController_inv"
  by (zpog_full; auto)

lemma "ChangeoverToNormalOperation() preserves R2 under ADSController_inv"
  by (zpog_full; auto)

lemma "FailSafeToNormalOperation() preserves R2 under ADSController_inv"
  by (zpog_full; auto)

(* REQ-ADS-007: power loss is accepted in both operating modes, so neither
   NormalOperation nor Changeover can ignore it. *)
definition R3 :: "ADSController \<Rightarrow> bool" where
  [z_defs]: "R3 s = (lens_get st s \<in> {NormalOperation, Changeover} \<longrightarrow>
                       powerLoss \<in> ADSController_inputs s)"

expr_constructor R3

lemma "Init establishes R3"
  by (zpog_full; expr_simp add: ADSController_inputs_by_mode; auto)

lemma "InitialToNormalOperation() preserves R3 under ADSController_inv"
  by (zpog_full; expr_simp add: ADSController_inputs_by_mode; auto)

lemma "NormalOperationToFailSafe() preserves R3 under ADSController_inv"
  by (zpog_full; expr_simp add: ADSController_inputs_by_mode; auto)

lemma "NormalOperationToChangeover() preserves R3 under ADSController_inv"
  by (zpog_full; expr_simp add: ADSController_inputs_by_mode; auto)

lemma "ChangeoverToFailSafe() preserves R3 under ADSController_inv"
  by (zpog_full; expr_simp add: ADSController_inputs_by_mode; auto)

lemma "ChangeoverToNormalOperation() preserves R3 under ADSController_inv"
  by (zpog_full; expr_simp add: ADSController_inputs_by_mode; auto)

lemma "FailSafeToNormalOperation() preserves R3 under ADSController_inv"
  by (zpog_full; expr_simp add: ADSController_inputs_by_mode; auto)

(* REQ-ADS-006: completing a changeover hands duty to the other bed. *)
lemma ChangeoverToNormalOperation_alternates:
  "H{activeDryer = \<guillemotleft>d\<guillemotright>} ChangeoverToNormalOperation() {_. activeDryer = \<guillemotleft>nextDryer d\<guillemotright>}"
  by (zpog_full; auto)


lemma NormalOperation_powerLoss_response:
  "H{activeDryer = \<guillemotleft>d\<guillemotright> \<and> tr = \<guillemotleft>t\<guillemotright>} NormalOperationToFailSafe()
    {_. st = FailSafe \<and> activeDryer = \<guillemotleft>d\<guillemotright> \<and>
         tr = \<guillemotleft>t\<guillemotright> @ [Event powerLoss, Event enterFailSafe, State FailSafe]}"
  by (zpog_full; auto)

lemma Changeover_powerLoss_response:
  "H{activeDryer = \<guillemotleft>d\<guillemotright> \<and> tr = \<guillemotleft>t\<guillemotright>} ChangeoverToFailSafe()
    {_. st = FailSafe \<and> activeDryer = \<guillemotleft>d\<guillemotright> \<and>
         tr = \<guillemotleft>t\<guillemotright> @ [Event powerLoss, Event enterFailSafe, State FailSafe]}"
  by (zpog_full; auto)

(* Every operation's destination mode, recorded events and bed selection.
   Only completing a changeover changes the bed (REQ-ADS-006); the recorded
   trace includes the output commands of each transition. *)
lemma InitialToNormalOperation_destination:
  "H{activeDryer = \<guillemotleft>d\<guillemotright> \<and> tr = \<guillemotleft>t\<guillemotright>} InitialToNormalOperation()
    {_. st = NormalOperation \<and> activeDryer = \<guillemotleft>d\<guillemotright> \<and>
         tr = \<guillemotleft>t\<guillemotright> @ [State NormalOperation]}"
  by (zpog_full; auto)

lemma NormalOperationToChangeover_destination:
  "H{activeDryer = \<guillemotleft>d\<guillemotright> \<and> tr = \<guillemotleft>t\<guillemotright>} NormalOperationToChangeover()
    {_. st = Changeover \<and> activeDryer = \<guillemotleft>d\<guillemotright> \<and>
         tr = \<guillemotleft>t\<guillemotright> @ [Event dewpointHigh, Event raiseAlarm, Event startChangeover, State Changeover]}"
  by (zpog_full; auto)

lemma ChangeoverToNormalOperation_destination:
  "H{activeDryer = \<guillemotleft>d\<guillemotright> \<and> tr = \<guillemotleft>t\<guillemotright>} ChangeoverToNormalOperation()
    {_. st = NormalOperation \<and> activeDryer = \<guillemotleft>nextDryer d\<guillemotright> \<and>
         tr = \<guillemotleft>t\<guillemotright> @ [Event changeoverComplete, State NormalOperation]}"
  by (zpog_full; auto)

lemma FailSafeToNormalOperation_destination:
  "H{activeDryer = \<guillemotleft>d\<guillemotright> \<and> tr = \<guillemotleft>t\<guillemotright>} FailSafeToNormalOperation()
    {_. st = NormalOperation \<and> activeDryer = \<guillemotleft>d\<guillemotright> \<and>
         tr = \<guillemotleft>t\<guillemotright> @ [Event backupRestored, Event restoreNormal, State NormalOperation]}"
  by (zpog_full; auto)

(* The stored trigger set must agree with the executable input interface. *)
definition InputsAgree :: "ADSController \<Rightarrow> bool" where
  [z_defs]: "InputsAgree s = (lens_get triggers s = ADSController_inputs s)"

expr_constructor InputsAgree

lemma "Init establishes InputsAgree"
  by (zpog_full; expr_simp add: ADSController_inputs_by_mode; auto)

lemma "InitialToNormalOperation() preserves InputsAgree under ADSController_inv"
  by (zpog_full; expr_simp add: ADSController_inputs_by_mode; auto)

lemma "NormalOperationToFailSafe() preserves InputsAgree under ADSController_inv"
  by (zpog_full; expr_simp add: ADSController_inputs_by_mode; auto)

lemma "NormalOperationToChangeover() preserves InputsAgree under ADSController_inv"
  by (zpog_full; expr_simp add: ADSController_inputs_by_mode; auto)

lemma "ChangeoverToFailSafe() preserves InputsAgree under ADSController_inv"
  by (zpog_full; expr_simp add: ADSController_inputs_by_mode; auto)

lemma "ChangeoverToNormalOperation() preserves InputsAgree under ADSController_inv"
  by (zpog_full; expr_simp add: ADSController_inputs_by_mode; auto)

lemma "FailSafeToNormalOperation() preserves InputsAgree under ADSController_inv"
  by (zpog_full; expr_simp add: ADSController_inputs_by_mode; auto)

definition [z_defs]: "ADSController_axioms = True"

lemma ADSController_deadlock_free: "ADSController_axioms  \<Longrightarrow> deadlock_free ADSControllerMachine"
  unfolding ADSControllerMachine_def ADSController_operations_def
  apply deadlock_free
  by (case_tac st; auto)
end
