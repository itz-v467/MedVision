import { ClinicalService } from "../services/clinicalService";

export const clinicalApi = {
  upload: ClinicalService.upload,
  encounters: ClinicalService.listEncounters,
  getEncounter: ClinicalService.getEncounter,
  finalizeSummary: ClinicalService.finalizeSummary,
  acknowledgeAlert: ClinicalService.acknowledgeAlert,
  deleteEncounter: ClinicalService.deleteEncounter,
  searchPatients: ClinicalService.searchPatients,
  previewPatientId: ClinicalService.previewPatientId,
};
