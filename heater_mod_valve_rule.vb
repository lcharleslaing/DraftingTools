' Heater Mod Valve iLogic Rule - NO BRASS COMPONENTS EVER
' Controls component visibility and BOM structure based on HEATER_MODEL and MOD_VALVE parameters
' ALWAYS uses stainless steel components - no brass regardless of mod valve setting

' No Mod Valve - Standard SS304 components (NO BRASS)
If HEATER_MODEL = "TE-100" And MOD_VALVE = "NO" Then
Component.Visible("NIPPLE (KEMCO) SS304, 40S, 1/4 X (SHORT) 1-1/2:6") = True
Component.Visible("NIPPLE (KEMCO) SS304, 40S, 1/4 X (SHORT) 1-1/2:5") = True
Component.Visible("ELBOW, 90, THREADED (KEMCO) SS304, 1/4:3") = True
Component.Visible("501-01-036 IFM PN4226 36.3PSI:1") = True
Component.Visible("504-02-016 NTS:1") = True
Component.InventorComponent("NIPPLE (KEMCO) SS304, 40S, 1/4 X (SHORT) 1-1/2:6").BOMStructure = BOMStructureEnum.kDefaultBOMStructure
Component.InventorComponent("NIPPLE (KEMCO) SS304, 40S, 1/4 X (SHORT) 1-1/2:5").BOMStructure = BOMStructureEnum.kDefaultBOMStructure
Component.InventorComponent("ELBOW, 90, THREADED (KEMCO) SS304, 1/4:3").BOMStructure = BOMStructureEnum.kDefaultBOMStructure
Component.InventorComponent("501-01-036 IFM PN4226 36.3PSI:1").BOMStructure = BOMStructureEnum.kDefaultBOMStructure
Component.InventorComponent("504-02-016 NTS:1").BOMStructure = BOMStructureEnum.kDefaultBOMStructure
'Parts Off - NO BRASS EVER
Component.Visible("1062111 PS-PT BRASS:1") = False
Component.Visible("1062112 PS-PT NSF:1") = False
Component.Visible("1062113 PS-PT SS316:1") = False
Component.InventorComponent("1062111 PS-PT BRASS:1").BOMStructure = BOMStructureEnum.kReferenceBOMStructure
Component.InventorComponent("1062112 PS-PT NSF:1").BOMStructure = BOMStructureEnum.kReferenceBOMStructure
Component.InventorComponent("1062113 PS-PT SS316:1").BOMStructure = BOMStructureEnum.kReferenceBOMStructure
End If

If HEATER_MODEL = "RM" And MOD_VALVE = "NO" Then
Component.Visible("NIPPLE (KEMCO) SS304, 40S, 1/4 X (SHORT) 1-1/2:6") = True
Component.Visible("NIPPLE (KEMCO) SS304, 40S, 1/4 X (SHORT) 1-1/2:5") = True
Component.Visible("ELBOW, 90, THREADED (KEMCO) SS304, 1/4:3") = True
Component.Visible("501-01-036 IFM PN4226 36.3PSI:1") = True
Component.Visible("504-02-016 NTS:1") = True
Component.InventorComponent("NIPPLE (KEMCO) SS304, 40S, 1/4 X (SHORT) 1-1/2:6").BOMStructure = BOMStructureEnum.kDefaultBOMStructure
Component.InventorComponent("NIPPLE (KEMCO) SS304, 40S, 1/4 X (SHORT) 1-1/2:5").BOMStructure = BOMStructureEnum.kDefaultBOMStructure
Component.InventorComponent("ELBOW, 90, THREADED (KEMCO) SS304, 1/4:3").BOMStructure = BOMStructureEnum.kDefaultBOMStructure
Component.InventorComponent("501-01-036 IFM PN4226 36.3PSI:1").BOMStructure = BOMStructureEnum.kDefaultBOMStructure
Component.InventorComponent("504-02-016 NTS:1").BOMStructure = BOMStructureEnum.kDefaultBOMStructure
'Parts Off - NO BRASS EVER
Component.Visible("1062111 PS-PT BRASS:1") = False
Component.Visible("1062112 PS-PT NSF:1") = False
Component.Visible("1062113 PS-PT SS316:1") = False
Component.InventorComponent("1062111 PS-PT BRASS:1").BOMStructure = BOMStructureEnum.kReferenceBOMStructure
Component.InventorComponent("1062112 PS-PT NSF:1").BOMStructure = BOMStructureEnum.kReferenceBOMStructure
Component.InventorComponent("1062113 PS-PT SS316:1").BOMStructure = BOMStructureEnum.kReferenceBOMStructure
End If

If HEATER_MODEL = "GP" And MOD_VALVE = "NO" Then
Component.Visible("NIPPLE (KEMCO) SS304, 40S, 1/4 X (SHORT) 1-1/2:6") = True
Component.Visible("NIPPLE (KEMCO) SS304, 40S, 1/4 X (SHORT) 1-1/2:5") = True
Component.Visible("ELBOW, 90, THREADED (KEMCO) SS304, 1/4:3") = True
Component.Visible("501-01-036 IFM PN4226 36.3PSI:1") = True
Component.Visible("504-02-016 NTS:1") = True
Component.InventorComponent("NIPPLE (KEMCO) SS304, 40S, 1/4 X (SHORT) 1-1/2:6").BOMStructure = BOMStructureEnum.kDefaultBOMStructure
Component.InventorComponent("NIPPLE (KEMCO) SS304, 40S, 1/4 X (SHORT) 1-1/2:5").BOMStructure = BOMStructureEnum.kDefaultBOMStructure
Component.InventorComponent("ELBOW, 90, THREADED (KEMCO) SS304, 1/4:3").BOMStructure = BOMStructureEnum.kDefaultBOMStructure
Component.InventorComponent("501-01-036 IFM PN4226 36.3PSI:1").BOMStructure = BOMStructureEnum.kDefaultBOMStructure
Component.InventorComponent("504-02-016 NTS:1").BOMStructure = BOMStructureEnum.kDefaultBOMStructure
'Parts Off - NO BRASS EVER
Component.Visible("1062111 PS-PT BRASS:1") = False
Component.Visible("1062112 PS-PT NSF:1") = False
Component.Visible("1062113 PS-PT SS316:1") = False
Component.InventorComponent("1062111 PS-PT BRASS:1").BOMStructure = BOMStructureEnum.kReferenceBOMStructure
Component.InventorComponent("1062112 PS-PT NSF:1").BOMStructure = BOMStructureEnum.kReferenceBOMStructure
Component.InventorComponent("1062113 PS-PT SS316:1").BOMStructure = BOMStructureEnum.kReferenceBOMStructure
End If

If HEATER_MODEL = "TE-NSF" And MOD_VALVE = "NO" Then
Component.Visible("NIPPLE (KEMCO) SS304, 40S, 1/4 X (SHORT) 1-1/2:6") = True
Component.Visible("NIPPLE (KEMCO) SS304, 40S, 1/4 X (SHORT) 1-1/2:5") = True
Component.Visible("ELBOW, 90, THREADED (KEMCO) SS304, 1/4:3") = True
Component.Visible("501-01-036 IFM PN4226 36.3PSI:1") = True
Component.Visible("504-02-016 NTS:1") = True
Component.InventorComponent("NIPPLE (KEMCO) SS304, 40S, 1/4 X (SHORT) 1-1/2:6").BOMStructure = BOMStructureEnum.kDefaultBOMStructure
Component.InventorComponent("NIPPLE (KEMCO) SS304, 40S, 1/4 X (SHORT) 1-1/2:5").BOMStructure = BOMStructureEnum.kDefaultBOMStructure
Component.InventorComponent("ELBOW, 90, THREADED (KEMCO) SS304, 1/4:3").BOMStructure = BOMStructureEnum.kDefaultBOMStructure
Component.InventorComponent("501-01-036 IFM PN4226 36.3PSI:1").BOMStructure = BOMStructureEnum.kDefaultBOMStructure
Component.InventorComponent("504-02-016 NTS:1").BOMStructure = BOMStructureEnum.kDefaultBOMStructure
'Parts Off - NO BRASS EVER
Component.Visible("1062111 PS-PT BRASS:1") = False
Component.Visible("1062112 PS-PT NSF:1") = False
Component.Visible("1062113 PS-PT SS316:1") = False
Component.InventorComponent("1062111 PS-PT BRASS:1").BOMStructure = BOMStructureEnum.kReferenceBOMStructure
Component.InventorComponent("1062112 PS-PT NSF:1").BOMStructure = BOMStructureEnum.kReferenceBOMStructure
Component.InventorComponent("1062113 PS-PT SS316:1").BOMStructure = BOMStructureEnum.kReferenceBOMStructure
End If

' Mod Valve YES - Only SS316 components (NO BRASS EVER)
If HEATER_MODEL = "RM" And MOD_VALVE = "YES" Then
Component.Visible("1062113 PS-PT SS316:1") = True
Component.InventorComponent("1062113 PS-PT SS316:1").BOMStructure = BOMStructureEnum.kDefaultBOMStructure
	
'Parts Off - NO BRASS EVER
Component.Visible("1062111 PS-PT BRASS:1") = False
Component.Visible("1062112 PS-PT NSF:1") = False
Component.Visible("NIPPLE (KEMCO) SS304, 40S, 1/4 X (SHORT) 1-1/2:6") = False
Component.Visible("NIPPLE (KEMCO) SS304, 40S, 1/4 X (SHORT) 1-1/2:5") = False
Component.Visible("ELBOW, 90, THREADED (KEMCO) SS304, 1/4:3") = False
Component.Visible("501-01-036 IFM PN4226 36.3PSI:1") = False
Component.Visible("504-02-016 NTS:1") = False

Component.InventorComponent("1062111 PS-PT BRASS:1").BOMStructure = BOMStructureEnum.kReferenceBOMStructure
Component.InventorComponent("1062112 PS-PT NSF:1").BOMStructure = BOMStructureEnum.kReferenceBOMStructure
Component.InventorComponent("NIPPLE (KEMCO) SS304, 40S, 1/4 X (SHORT) 1-1/2:6").BOMStructure = BOMStructureEnum.kReferenceBOMStructure
Component.InventorComponent("NIPPLE (KEMCO) SS304, 40S, 1/4 X (SHORT) 1-1/2:5").BOMStructure = BOMStructureEnum.kReferenceBOMStructure
Component.InventorComponent("ELBOW, 90, THREADED (KEMCO) SS304, 1/4:3").BOMStructure = BOMStructureEnum.kReferenceBOMStructure
Component.InventorComponent("501-01-036 IFM PN4226 36.3PSI:1").BOMStructure = BOMStructureEnum.kReferenceBOMStructure
Component.InventorComponent("504-02-016 NTS:1").BOMStructure = BOMStructureEnum.kReferenceBOMStructure
End If

If HEATER_MODEL = "GP" And MOD_VALVE = "YES" Then
Component.Visible("1062113 PS-PT SS316:1") = True
Component.InventorComponent("1062113 PS-PT SS316:1").BOMStructure = BOMStructureEnum.kDefaultBOMStructure
	
'Parts Off - NO BRASS EVER
Component.Visible("1062111 PS-PT BRASS:1") = False
Component.Visible("1062112 PS-PT NSF:1") = False
Component.Visible("NIPPLE (KEMCO) SS304, 40S, 1/4 X (SHORT) 1-1/2:6") = False
Component.Visible("NIPPLE (KEMCO) SS304, 40S, 1/4 X (SHORT) 1-1/2:5") = False
Component.Visible("ELBOW, 90, THREADED (KEMCO) SS304, 1/4:3") = False
Component.Visible("501-01-036 IFM PN4226 36.3PSI:1") = False
Component.Visible("504-02-016 NTS:1") = False

Component.InventorComponent("1062111 PS-PT BRASS:1").BOMStructure = BOMStructureEnum.kReferenceBOMStructure
Component.InventorComponent("1062112 PS-PT NSF:1").BOMStructure = BOMStructureEnum.kReferenceBOMStructure
Component.InventorComponent("NIPPLE (KEMCO) SS304, 40S, 1/4 X (SHORT) 1-1/2:6").BOMStructure = BOMStructureEnum.kReferenceBOMStructure
Component.InventorComponent("NIPPLE (KEMCO) SS304, 40S, 1/4 X (SHORT) 1-1/2:5").BOMStructure = BOMStructureEnum.kReferenceBOMStructure
Component.InventorComponent("ELBOW, 90, THREADED (KEMCO) SS304, 1/4:3").BOMStructure = BOMStructureEnum.kReferenceBOMStructure
Component.InventorComponent("501-01-036 IFM PN4226 36.3PSI:1").BOMStructure = BOMStructureEnum.kReferenceBOMStructure
Component.InventorComponent("504-02-016 NTS:1").BOMStructure = BOMStructureEnum.kReferenceBOMStructure
End If

If HEATER_MODEL = "TE-100" And MOD_VALVE = "YES" Then
Component.Visible("1062113 PS-PT SS316:1") = True
Component.InventorComponent("1062113 PS-PT SS316:1").BOMStructure = BOMStructureEnum.kDefaultBOMStructure
	
'Parts Off - NO BRASS EVER
Component.Visible("1062111 PS-PT BRASS:1") = False
Component.Visible("1062112 PS-PT NSF:1") = False
Component.Visible("NIPPLE (KEMCO) SS304, 40S, 1/4 X (SHORT) 1-1/2:6") = False
Component.Visible("NIPPLE (KEMCO) SS304, 40S, 1/4 X (SHORT) 1-1/2:5") = False
Component.Visible("ELBOW, 90, THREADED (KEMCO) SS304, 1/4:3") = False
Component.Visible("501-01-036 IFM PN4226 36.3PSI:1") = False
Component.Visible("504-02-016 NTS:1") = False

Component.InventorComponent("1062111 PS-PT BRASS:1").BOMStructure = BOMStructureEnum.kReferenceBOMStructure
Component.InventorComponent("1062112 PS-PT NSF:1").BOMStructure = BOMStructureEnum.kReferenceBOMStructure
Component.InventorComponent("NIPPLE (KEMCO) SS304, 40S, 1/4 X (SHORT) 1-1/2:6").BOMStructure = BOMStructureEnum.kReferenceBOMStructure
Component.InventorComponent("NIPPLE (KEMCO) SS304, 40S, 1/4 X (SHORT) 1-1/2:5").BOMStructure = BOMStructureEnum.kReferenceBOMStructure
Component.InventorComponent("ELBOW, 90, THREADED (KEMCO) SS304, 1/4:3").BOMStructure = BOMStructureEnum.kReferenceBOMStructure
Component.InventorComponent("501-01-036 IFM PN4226 36.3PSI:1").BOMStructure = BOMStructureEnum.kReferenceBOMStructure
Component.InventorComponent("504-02-016 NTS:1").BOMStructure = BOMStructureEnum.kReferenceBOMStructure
End If

If HEATER_MODEL = "TE-NSF" And MOD_VALVE = "YES" Then
Component.Visible("1062113 PS-PT SS316:1") = True
Component.InventorComponent("1062113 PS-PT SS316:1").BOMStructure = BOMStructureEnum.kDefaultBOMStructure
	
'Parts Off - NO BRASS EVER
Component.Visible("1062111 PS-PT BRASS:1") = False
Component.Visible("1062112 PS-PT NSF:1") = False
Component.Visible("NIPPLE (KEMCO) SS304, 40S, 1/4 X (SHORT) 1-1/2:6") = False
Component.Visible("NIPPLE (KEMCO) SS304, 40S, 1/4 X (SHORT) 1-1/2:5") = False
Component.Visible("ELBOW, 90, THREADED (KEMCO) SS304, 1/4:3") = False
Component.Visible("501-01-036 IFM PN4226 36.3PSI:1") = False
Component.Visible("504-02-016 NTS:1") = False

Component.InventorComponent("1062111 PS-PT BRASS:1").BOMStructure = BOMStructureEnum.kReferenceBOMStructure
Component.InventorComponent("1062112 PS-PT NSF:1").BOMStructure = BOMStructureEnum.kReferenceBOMStructure
Component.InventorComponent("NIPPLE (KEMCO) SS304, 40S, 1/4 X (SHORT) 1-1/2:6").BOMStructure = BOMStructureEnum.kReferenceBOMStructure
Component.InventorComponent("NIPPLE (KEMCO) SS304, 40S, 1/4 X (SHORT) 1-1/2:5").BOMStructure = BOMStructureEnum.kReferenceBOMStructure
Component.InventorComponent("ELBOW, 90, THREADED (KEMCO) SS304, 1/4:3").BOMStructure = BOMStructureEnum.kReferenceBOMStructure
Component.InventorComponent("501-01-036 IFM PN4226 36.3PSI:1").BOMStructure = BOMStructureEnum.kReferenceBOMStructure
Component.InventorComponent("504-02-016 NTS:1").BOMStructure = BOMStructureEnum.kReferenceBOMStructure
End If
