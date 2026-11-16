"""
accounts.py - the buyer registry ("account spine").

One row per public body that matters to JazzWorld. `rx` is matched against the
canonical buyer string (lower case, punctuation removed). `digital` marks bodies that
hold a digitisation budget (IT boards, regulators, telecom, banks, large utilities).
`group` lets several buyers share one relationship record or one signal
(for example every DISCO shares the "DISCOs" bill-collection relationship).

Tier is NOT typed in by hand. It is derived in the engine:
    A  JazzWorld already has a public relationship with the buyer (client, win, partnership)
       OR the buyer is named in a tracked signal or prediction
    B  digital budget holder with no relationship or signal on file
    C  everyone else
"""

ACCOUNTS = [
    # federal digital core
    ("ntc", "National Telecommunication Corporation (NTC)", r"national telecommunication corporation|\bntc\b", True, "Telecom & IT", "Federal", ""),
    ("usf", "Universal Service Fund (USF)", r"universal service fund|\busf\b", True, "Telecom & IT", "Federal", ""),
    ("moitt", "Ministry of IT & Telecom (MoITT)", r"ministry of it and telecom|ministry of information technology|\bmoitt\b|it and telecom division", True, "Telecom & IT", "Federal", ""),
    ("pta", "Pakistan Telecommunication Authority (PTA)", r"pakistan telecommunication authority|\bpta\b", True, "Telecom & IT", "Federal", ""),
    ("fab", "Frequency Allocation Board (FAB)", r"frequency allocation board|\bfab\b", True, "Telecom & IT", "Federal", ""),
    ("nitb", "National Information Technology Board (NITB)", r"national information technology board|\bnitb\b", True, "Telecom & IT", "Federal", ""),
    ("pda", "Pakistan Digital Authority (PDA)", r"pakistan digital authority", True, "Telecom & IT", "Federal", ""),
    ("ignite", "Ignite National Technology Fund", r"\bignite\b|national technology fund", True, "Telecom & IT", "Federal", ""),
    ("pseb", "Pakistan Software Export Board (PSEB)", r"pakistan software export board|\bpseb\b", True, "Telecom & IT", "Federal", ""),
    ("stza", "Special Technology Zones Authority (STZA)", r"special technology zones authority|\bstza\b", True, "Telecom & IT", "Federal", ""),
    ("ntisb", "NTISB / Communications Security", r"\bntisb\b|communications security|national telecommunication and information technology security", True, "Telecom & IT", "Federal", ""),
    ("nadra", "NADRA", r"\bnadra\b|national database", True, "Identity & Registration", "Federal", ""),
    ("fbr", "Federal Board of Revenue (FBR)", r"federal board of revenue|\bfbr\b|revenue division|inland revenue|collectorate of customs|customs enforcement|model customs", True, "Revenue & Finance", "Federal", "fbr"),
    ("pral", "Pakistan Revenue Automation (PRAL)", r"pakistan revenue automation|\bpral\b", True, "Revenue & Finance", "Federal", "fbr"),
    ("psw", "Pakistan Single Window (PSW)", r"pakistan single window|\bpsw\b", True, "Revenue & Finance", "Federal", ""),
    ("sbp", "State Bank of Pakistan (SBP)", r"state bank of pakistan|\bsbp\b|sbp banking services|\bnibaf\b", True, "Banking & Insurance", "Federal", ""),
    ("secp", "Securities & Exchange Commission (SECP)", r"securities and exchange commission|\bsecp\b", True, "Banking & Insurance", "Federal", ""),
    ("nbp", "National Bank of Pakistan (NBP)", r"national bank of pakistan|\bnbp\b", True, "Banking & Insurance", "Federal", ""),
    ("ztbl", "Zarai Taraqiati Bank (ZTBL)", r"zarai taraqiati|\bztbl\b", True, "Banking & Insurance", "Federal", ""),
    ("hbfc", "House Building Finance Company (HBFC)", r"house building finance|\bhbfc\b", True, "Banking & Insurance", "Federal", ""),
    ("cdns", "National Savings (CDNS)", r"national savings|\bcdns\b", True, "Banking & Insurance", "Federal", ""),
    ("slic", "State Life Insurance Corporation", r"state life", True, "Banking & Insurance", "Federal", ""),
    ("nit", "National Investment Trust (NIT)", r"national investment trust|\bnit\b", True, "Banking & Insurance", "Federal", ""),
    ("bisp", "Benazir Income Support Programme (BISP)", r"benazir income support|\bbisp\b", True, "Social Protection", "Federal", ""),
    ("pass", "Poverty Alleviation & Social Safety Division", r"poverty alleviation", True, "Social Protection", "Federal", ""),
    ("ecp", "Election Commission of Pakistan", r"election commission", True, "Governance", "Federal", ""),
    ("ppra", "Federal PPRA", r"public procurement regulatory authority \(ppra\)|federal public procurement|^ppra", True, "Governance", "Federal", ""),
    ("pid", "Ministry of Information & Broadcasting", r"information and broadcasting|press information", False, "Governance", "Federal", ""),
    ("planning", "Planning Commission / MoPD&SI", r"ministry of planning|planning commission", True, "Governance", "Federal", ""),
    ("finance", "Finance Division", r"finance division|ministry of finance", True, "Revenue & Finance", "Federal", ""),
    ("cabinet", "Cabinet Division", r"cabinet division", False, "Governance", "Federal", ""),
    ("ombudsman", "Federal Ombudsman offices", r"ombuds|mohtasib", False, "Governance", "Federal", ""),
    # law enforcement and cities
    ("ictpolice", "Islamabad Police / Safe City Islamabad", r"islamabad police|ict police|safe city islamabad|capital territory police|islamabad capital territory police", True, "Law Enforcement & Cities", "Federal", "smartisb"),
    ("cda", "Capital Development Authority (CDA)", r"capital development authority|\bcda\b|metropolitan corporation islamabad", True, "Law Enforcement & Cities", "Federal", "smartisb"),
    ("ictadmin", "ICT Administration", r"ict administration|islamabad capital territory administration|chief commissioner", True, "Law Enforcement & Cities", "Federal", "smartisb"),
    ("interior", "Ministry of Interior", r"ministry of interior", False, "Law Enforcement & Cities", "Federal", "smartisb"),
    ("nhmp", "National Highways & Motorway Police (NHMP)", r"motorway police|\bnhmp\b", True, "Law Enforcement & Cities", "Federal", "traffic"),
    ("traffic", "Traffic Police", r"traffic police", True, "Law Enforcement & Cities", "", "traffic"),
    ("nha", "National Highway Authority (NHA)", r"national highway authority|\bnha\b", True, "Transport", "Federal", ""),
    ("railways", "Pakistan Railways", r"pakistan railways|railways", True, "Transport", "Federal", ""),
    ("paa", "Pakistan Airports Authority / CAA", r"pakistan airports authority|civil aviation|\bpaa\b|\bcaa\b", True, "Transport", "Federal", ""),
    ("pia", "Pakistan International Airlines (PIA)", r"pakistan international airlines|\bpia\b|\bpiacl\b", True, "Transport", "Federal", ""),
    ("kpt", "Port authorities (KPT, PQA, GPA)", r"karachi port trust|\bkpt\b|port qasim|gwadar port", False, "Transport", "Federal", ""),
    # energy
    ("powerdiv", "Power Division", r"power division", True, "Energy & Utilities", "Federal", "disco"),
    ("ngc", "National Grid Company (NGC / NTDC)", r"national grid company|\bngc\b|\bntdc\b|national transmission", True, "Energy & Utilities", "Federal", ""),
    ("iesco", "IESCO", r"\biesco\b|islamabad electric", True, "Energy & Utilities", "Federal", "disco"),
    ("lesco", "LESCO", r"\blesco\b|lahore electric", True, "Energy & Utilities", "Federal", "disco"),
    ("mepco", "MEPCO", r"\bmepco\b|multan electric", True, "Energy & Utilities", "Federal", "disco"),
    ("pesco", "PESCO", r"\bpesco\b|peshawar electric", True, "Energy & Utilities", "Federal", "disco"),
    ("gepco", "GEPCO", r"\bgepco\b|gujranwala electric", True, "Energy & Utilities", "Federal", "disco"),
    ("fesco", "FESCO", r"\bfesco\b|faisalabad electric", True, "Energy & Utilities", "Federal", "disco"),
    ("hesco", "HESCO", r"\bhesco\b|hyderabad electric", True, "Energy & Utilities", "Federal", "disco"),
    ("sepco", "SEPCO", r"\bsepco\b|sukkur electric", True, "Energy & Utilities", "Federal", "disco"),
    ("qesco", "QESCO", r"\bqesco\b|quetta electric", True, "Energy & Utilities", "Federal", "disco"),
    ("tesco", "TESCO", r"\btesco\b|tribal areas electric", True, "Energy & Utilities", "Federal", "disco"),
    ("wapda", "WAPDA", r"\bwapda\b|water and power development", True, "Energy & Utilities", "Federal", ""),
    ("sngpl", "Sui Northern Gas (SNGPL)", r"\bsngpl\b|sui northern", True, "Energy & Utilities", "Federal", ""),
    ("ssgc", "Sui Southern Gas (SSGC)", r"\bssgc\b|sui southern", True, "Energy & Utilities", "Federal", ""),
    ("ogdcl", "OGDCL", r"\bogdcl\b|oil and gas development", True, "Energy & Utilities", "Federal", ""),
    ("ppl", "Pakistan Petroleum (PPL)", r"pakistan petroleum|\bppl\b", True, "Energy & Utilities", "Federal", ""),
    ("pso", "Pakistan State Oil (PSO)", r"pakistan state oil|\bpso\b", True, "Energy & Utilities", "Federal", ""),
    ("parco", "PARCO", r"\bparco\b|pak arab refinery", True, "Energy & Utilities", "Federal", ""),
    ("ogra", "OGRA", r"\bogra\b|oil and gas regulatory", False, "Energy & Utilities", "Federal", ""),
    ("nepra", "NEPRA", r"\bnepra\b|electric power regulatory", False, "Energy & Utilities", "Federal", ""),
    # education and health
    ("hec", "Higher Education Commission (HEC)", r"higher education commission|\bhec\b", True, "Education", "Federal", "edu"),
    ("ibcc", "Inter Boards Coordination Commission (IBCC)", r"inter boards|\bibcc\b", False, "Education", "Federal", "edu"),
    ("aiou", "Allama Iqbal Open University (AIOU)", r"allama iqbal open university|\baiou\b", False, "Education", "Federal", "edu"),
    ("nust", "NUST", r"\bnust\b|national university of sciences", False, "Education", "Federal", "edu"),
    ("comsats", "COMSATS University", r"comsats", False, "Education", "Federal", "edu"),
    ("uni", "Public universities and boards", r"university|\bbise\b|board of intermediate|institute of", False, "Education", "", "edu"),
    ("fde", "Federal Education & Professional Training", r"federal education|federal directorate of education|\bnavttc\b|\bnchd\b", False, "Education", "Federal", "edu"),
    ("pmd", "Pakistan Meteorological Department (PMD)", r"meteorological|\bpmd\b", True, "Governance", "Federal", ""),
    ("ndma", "NDMA / disaster management", r"disaster management|\bndma\b|\bpdma\b", True, "Governance", "", "pdma"),
    ("tdap", "Trade Development Authority (TDAP)", r"trade development authority|\btdap\b", False, "Governance", "Federal", ""),
    # provinces
    ("pitb", "Punjab Information Technology Board (PITB)", r"punjab information technology board|\bpitb\b", True, "Telecom & IT", "Punjab", "punjab"),
    ("psca", "Punjab Safe Cities Authority (PSCA)", r"punjab safe cit|\bpsca\b", True, "Law Enforcement & Cities", "Punjab", "punjab"),
    ("plra", "Punjab Land Records Authority (PLRA)", r"punjab land records|\bplra\b", True, "Governance", "Punjab", "punjab"),
    ("sedpunjab", "School Education Department, Punjab", r"school education department|\bpesrp\b|pmiu pesrp", True, "Education", "Punjab", "punjab"),
    ("zakatpb", "Zakat & Ushr Department, Punjab", r"zakat", False, "Social Protection", "Punjab", "punjab"),
    ("agripb", "Agriculture Department, Punjab", r"agriculture department", False, "Agriculture", "Punjab", "punjab"),
    ("punjab", "Government of Punjab (other)", r"punjab", False, "Provincial", "Punjab", "punjab"),
    ("kpitb", "KP Information Technology Board (KPITB)", r"khyber pakhtunkhwa information technology board|\bkpitb\b|kp it board", True, "Telecom & IT", "KP", "kp"),
    ("kp", "Government of Khyber Pakhtunkhwa (other)", r"khyber pakhtunkhwa|\bkp\b|\bkpk\b|peshawar", False, "Provincial", "KP", "kp"),
    ("sitc", "Sindh IT Company / S&IT Department", r"sindh information technology|sindh it company|science and information technology department", True, "Telecom & IT", "Sindh", "sindh"),
    ("sindh", "Government of Sindh (other)", r"sindh", False, "Provincial", "Sindh", "sindh"),
    ("bppra", "Balochistan PPRA", r"balochistan public procurement|\bbppra\b", True, "Governance", "Balochistan", "balochistan"),
    ("balochistan", "Government of Balochistan (other)", r"balochistan", False, "Provincial", "Balochistan", "balochistan"),
    ("nrsp", "National Rural Support Programme (NRSP)", r"rural support programme|\bnrsp\b", False, "Social Protection", "", ""),
    ("defence", "Defence procurement directorates", r"directorate of procurement|\bdgp\b|defence|army|navy|air force|battalion|regiment|ordnance|\bpaf\b|\bpof\b|\bhit\b|\bnescom\b|\bmes\b|engineer in chief|frontier works|\bfwo\b|\bnlc\b|\bsco\b|special communication", False, "Defence", "Federal", ""),
]


def to_json():
    # A bucket is a category of buyers, not one buyer. The page counts each body inside it separately.
    BUCKETS = {"uni", "defence", "punjab", "kp", "sindh", "balochistan", "ombudsman", "kpt", "traffic"}
    return [{"id": a[0], "name": a[1], "rx": a[2], "digital": a[3], "sector": a[4], "province": a[5], "group": a[6], "bucket": a[0] in BUCKETS} for a in ACCOUNTS]
