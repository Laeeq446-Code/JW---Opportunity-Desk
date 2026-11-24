"""
rules.py - the matching rules for every catalogue product.

This file is the single place where "what counts as evidence" is written down.
It is exported as data (catalogue.js) and read by engine.js, so the page can show
every rule to the user and nothing is hidden in code.

Term notation
    "phrase"      STRONG evidence. One hit is enough to say the buyer is asking for the product.
    "?phrase"     SUPPORT evidence. Generic word. Never enough on its own.
    trailing *    prefix match  ("licen*" matches licence, licenses, licensing)
    plain terms also match a plural s / es.

Text is compared after lower-casing and replacing every non-alphanumeric character
with a space, so "Wi-Fi", "wi fi" and "WI_FI" are the same thing.

"not" maps a term to a context pattern. When the context is present in the tender,
that term is ignored. This is how "SMS" (sales meter station) at a gas company or
"GIS" (gas insulated switchgear) at a power company are kept out.

mode
    own      JazzWorld sells this as its own service and can lead the bid.
    partner  JazzWorld needs an OEM or delivery partner to bid (resale, build work).
"""

RULES = {
    # ───────────────────────────── CONNECTIVITY ─────────────────────────────
    "c5g": {
        "mode": "own",
        "terms": [
            "wireless data service*", "data connections", "lte connection*", "4g connection*", "5g connection*",
            "sim card*", "data sim*", "sims", "corporate sim*", "mobile connection*", "cellular connection*",
            "cellular service*", "gsm connection*", "gsm service*", "postpaid connection*", "mobile sim*",
            "mobile data", "mobile broadband", "mifi", "mi fi", "4g device*", "4g dongle*", "internet device*",
            "wireless internet device*", "closed user group", "cug", "esim", "e sim", "mobile phone connection*",
            "voice and data package*", "mobile package*", "cellular package*", "gsm sim*", "data connection*",
            "mobile internet", "cellular data", "telecom operator*", "cellular mobile operator*", "cmo", "cmos",
            "?4g", "?5g", "?lte", "?gsm", "?cellular", "?postpaid", "?prepaid", "?smartphone*", "?mobile phone*",
            "?handset*", "?data package*", "?internet package*",
        ],
        "not": {"cmo": "chief medical|medical officer", "cmos": "sensor|camera|battery", "sims": "school information|student information"},
    },
    "cbrap": {
        "mode": "own",
        "terms": [
            "airtime", "mobile top up*", "mobile load", "mobile balance", "easyload", "easy load", "free data",
            "data incentive*", "mobile recharge", "scratch card*", "bulk airtime",
            "?incentive*", "?reward*", "?loyalty", "?data bundle*",
        ],
        "not": {"scratch card*": "printing"},
    },
    "cnet": {
        "mode": "own",
        "terms": [
            "internet service*", "internet connection*", "internet connectivity", "internet bandwidth",
            "internet link*", "dedicated internet", "internet facility", "internet access", "internet leased line*",
            "broadband service*", "broadband connection*", "broadband internet", "internet service provider*", "isp",
            "isps", "bandwidth", "ip transit", "ddos", "public ip*", "ipv4", "ipv6", "ip address*", "web hosting",
            "website hosting", "domain hosting", "domain and hosting", "managed dns", "dns hosting",
            "internet subscription", "internet circuit*", "primary internet", "backup internet", "redundant internet",
            "?internet", "?connectivity", "?hosting", "?domain", "?dns",
        ],
    },
    "cfib": {
        "mode": "own",
        "terms": [
            "direct link*", "ofc network*", "laying of ofc",
            "mpls", "ip vpn", "ipvpn", "leased line*", "dark fiber", "dark fibre", "point to point link*",
            "p2p link*", "data link*", "wan link*", "wan connectivity", "wide area network", "intranet link*",
            "metro ethernet", "dplc", "iplc", "backhaul", "radio link*", "microwave link*", "vsat", "satellite link*",
            "satellite connectivity", "satellite internet", "satellite bandwidth", "network connectivity",
            "connectivity service*", "connectivity solution*", "media connectivity", "fiber connectivity",
            "fibre connectivity", "fiber link*", "fibre link*", "ofc link*", "ofc connectivity", "optical fiber link*",
            "optical fibre link*", "fiber optic link*", "fibre optic link*", "fiber optic connectivity",
            "last mile", "layer 2 link*", "layer 3 mpls", "inter office connectivity", "branch connectivity",
            "site to site", "data connectivity", "dedicated link*", "connectivity link*", "communication link*",
            "data circuit*", "lan wan connectivity",
            "?fiber", "?fibre", "?ofc", "?optical", "?wan", "?vpn", "?link*", "?connectivity", "?microwave", "?satellite",
        ],
        "block": ["power", "civil"],
    },
    "cvoice": {
        "mode": "own",
        "terms": [
            "sip trunk*", "pri line*", "e1 line*", "uan", "toll free", "ip telephony", "voip", "ip pbx", "ippbx",
            "ip pabx", "pabx", "epabx", "pbx", "telephone exchange", "hosted pbx", "call cent*", "contact cent*",
            "helpline", "ivr", "unified communication*", "telephony", "landline*", "telephone line*", "voice gateway*",
            "avaya", "ip phone*", "telephone connection*", "voice service*", "call recording", "telephone service*",
            "?telephone", "?voice", "?exchange", "?agent*",
        ],
        "not": {"uan": "university|urea", "telephone exchange": "building|construction|renovation", "exchange": "stock|foreign|heat"},
    },
    "csdn": {
        "mode": "own",
        "terms": [
            "sd wan", "sdwan", "managed wifi", "managed wi fi", "wifi network", "wi fi network", "wifi solution*",
            "wi fi solution*", "wifi service*", "wi fi service*", "wifi connectivity", "wi fi connectivity",
            "wifi hotspot*", "wi fi hotspot*", "hotspot*", "campus wifi", "wireless network", "wireless lan", "wlan",
            "wireless access point*", "wifi access point*", "wi fi access point*", "wifi", "wi fi", "wifi system",
            "wireless controller*", "wifi infrastructure", "indoor access point*", "outdoor access point*",
            "?lan", "?wireless", "?access point*", "?router*",
        ],
        "not": {"hotspot*": "polio|dengue|crime|disease"},
    },
    "cmng": {
        "mode": "own",
        "terms": [
            "ntp appliance*", "ntp server*",
            "network monitoring", "nms", "noc", "network operations cent*", "network operation cent*", "network audit",
            "network design", "managed network", "network management", "network maintenance",
            "maintenance of network", "network support", "cisco", "network device*", "network equipment",
            "networking equipment", "network infrastructure", "core switch*", "network switch*", "lan wan",
            "structured cabling", "active network", "passive network", "network upgrad*", "campus network",
            "local area network", "lan infrastructure", "lan solution", "layer 2 switch*", "layer 3 switch*",
            "managed switch*", "ethernet switch*", "network cabling", "networking of", "network revamp*",
            "data networking", "juniper", "aruba", "network refresh", "network installation", "networking",
            "it network", "computer network", "data network", "lan cabling", "network rack*", "poe switch*",
            "?network", "?switch*", "?managed service*", "?sla", "?maintenance", "?cabling",
        ],
        "block": ["power", "civil", "gas", "water"],
        "not": {"noc": "no objection|certificate", "networking": "event|session|business networking",
                "network equipment": "kv|grid|electric", "network infrastructure": "road|water|gas|sewer|vapt|penetration|vulnerability"},
    },
    "cftth": {
        "mode": "own",
        "terms": [
            "ftth", "fttx", "fiber to the home", "fibre to the home", "gpon", "epon", "xpon", "triple play",
            "fiber to the premises", "fibre to the premises", "ont", "olt",
            "?housing", "?bras",
        ],
        "not": {"ont": "ontario", "olt": "oil"},
    },
    "crural": {
        "mode": "own",
        "terms": [
            "ng bsd", "ngbsd", "next generation broadband for sustainable development", "broadband for sustainable development",
            "ng ofns", "optic fiber network and services", "unserved", "underserved", "under served", "un served",
            "mauza*", "rural broadband", "rural telephony", "broadband coverage", "mobile broadband coverage",
            "4g coverage", "cellular coverage", "mobile coverage", "universal service", "usf lot*",
            "rural telecom*", "broadband services in", "telecom infrastructure", "telecommunication infrastructure",
            "?rural", "?broadband", "?usf", "?coverage",
        ],
    },

    # ───────────────────────────── ENTERPRISE SOLUTIONS ─────────────────────────────
    "gcloud": {
        "mode": "own",
        "terms": [
            "cloud", "cloud service*", "cloud hosting", "cloud infrastructure", "cloud computing", "cloud platform",
            "cloud solution*", "cloud subscription", "cloud migration", "public cloud", "private cloud",
            "hybrid cloud", "sovereign cloud", "iaas", "paas", "infrastructure as a service", "platform as a service",
            "virtual machine*", "virtual private server*", "vps", "cloud storage", "object storage", "dbaas",
            "database as a service", "hosting service*", "managed hosting", "server hosting", "gpu as a service",
            "compute as a service", "data center hosting", "data centre hosting", "virtual data cent*",
            "virtual server*", "hosting of", "hosting and", "cloud based",
            "?hosting", "?server*", "?storage", "?virtuali*", "?vmware", "?compute", "?hci", "?hyper converged", "?gpu",
        ],
        "not": {"cloud": "cloud seeding|cloud burst|cloudburst|cloud ?engine", "hosting of": "event|dinner|conference|ceremony|delegation|guests",
                "hosting and": "event|dinner|catering|ceremony"},
    },
    "gdr": {
        "mode": "own",
        "terms": [
            "data cent* maintenance", "support services for data cent*", "migration of existing data cent*", "data cent* on turnkey", "veeam", "commvault",
            "disaster recovery", "dr site", "dr data cent*", "backup solution*", "backup service*",
            "backup as a service", "data backup", "offline backup", "backup and recovery", "backup software",
            "colocation", "co location", "rack space", "business continuity", "replication",
            "data cent* colocation", "data cent* hosting", "establishment of data cent*", "data cent* facility",
            "data cent* services", "data cent* infrastructure", "upgradation of data cent*", "modular data cent*",
            "containerized data cent*", "data cent* space", "tier 3 data cent*", "data cent* establishment",
            "tape library", "backup appliance*", "backup storage", "tier iii", "tier 3 data", "server room",
            "dr drill", "disaster recovery as a service", "draas",
            "?backup", "?rack*", "?recovery", "?ups", "?precision cooling", "?data cent*", "?datacent*",
        ],
        "not": {"replication": "seed|virus|dna", "server room": "air conditioner|hvac|fire suppression|renovation|civil|fals",
                "backup solution*": "power|solar|generator|battery"},
    },
    "gsoc": {
        "mode": "own",
        "terms": [
            "pen testing", "pentest*", "red teaming", "security assessment", "ngaf", "sangfor", "network detection and response", "ndr", "xdr",
            "soc", "csoc", "security operations cent*", "security operation cent*", "managed security", "siem", "soar",
            "cyber security", "cybersecurity", "cyber*", "information security", "penetration test*", "vapt",
            "vulnerability assessment", "threat intelligence", "ddos protection", "anti ddos", "endpoint security",
            "endpoint protection", "endpoint detection", "edr", "xdr", "ndr", "mdr", "firewall*", "ngfw", "waf",
            "web application firewall", "fortinet", "fortigate", "forti*", "palo alto", "antivirus", "anti virus",
            "email security", "web security", "server security", "dlp", "data loss prevention", "pam",
            "privileged access", "identity and access", "iam", "network access control", "nac", "zero trust",
            "it security", "iso 27001", "malware", "sandboxing", "nessus", "brand protection", "kaspersky", "sophos",
            "trend micro", "crowdstrike", "data diode", "intrusion", "ips ids", "ids ips", "spam protection",
            "email gateway", "security audit of", "it audit", "is audit", "load balancer*", "ssl certificate*",
            "network security", "security solution*", "utm", "unified threat", "security assessment",
            "?security", "?threat", "?endpoint", "?audit",
        ],
        "not": {
            "soc": "society|social", "pam": "pamphlet", "nac": "national accountability|nac building", "iam": "i am",
            "cyber*": "cyber insurance|cyber and digital insurance|cyber liability", "intrusion": "water|saline|sea",
            "security solution*": "guard|physical|perimeter|fence|walk through|metal detector|scanner|barrier",
            "security audit of": "building|fire|structur", "it audit": "internal audit firm|chartered accountant",
            "utm": "university", "forti*": "fortified|fortification|fortnight",
        },
    },
    "glic": {
        "mode": "partner",
        "terms": [
            "microsoft 365", "office 365", "m365", "o365", "microsoft licen*", "microsoft office", "ms office",
            "windows licen*", "windows server", "sql server", "software licen*", "licen* renewal", "renewal of licen*",
            "subscription renewal", "renewal of subscription", "enterprise agreement", "odoo", "email solution*",
            "email hosting", "email service*", "collaboration suite", "google workspace", "zoom licen*", "adobe",
            "autocad", "licenses", "licences", "microsoft", "oracle licen*", "red hat", "suse", "vmware licen*",
            "antivirus licen*", "software subscription*", "annual subscription", "volume licen*", "microsoft teams",
            "software renewal", "license subscription", "licence subscription", "exchange online", "sharepoint",
            "?licen*", "?subscription*", "?email", "?software", "?sql", "?linux", "?oracle", "?renewal",
        ],
        "not": {"licenses": "driving|arms|drug|fishing|mining licen", "licences": "driving|arms|drug|fishing|mining licen",
                "annual subscription": "journal|newspaper|magazine|membership|book", "adobe": "construction"},
    },
    "gsi": {
        "mode": "partner",
        "terms": [
            "e commerce marketplace", "marketplace technology", "official website", "website design*", "website revamp*", "application performance monitoring", "database performance monitoring", "augmented reality", "virtual reality",
            "software development", "application development", "development of software", "development of application",
            "web portal", "portal development", "development of portal", "development of web", "website development",
            "development of website", "web development", "web application*", "mobile app*", "mobile application*",
            "management information system", "mis", "erp", "enterprise resource planning", "hrmis", "hmis", "lmis",
            "pmis", "fmis", "emis", "e office", "eoffice", "e governance", "e government", "digital transformation",
            "digitization", "digitisation", "digitalization", "digitalisation", "digitiz*", "digitis*", "automation of",
            "system integration", "systems integration", "system integrator", "turnkey solution", "software solution*",
            "information system*", "it consultan*", "it solution*", "it project*", "it support", "it services",
            "it infrastructure", "it helpdesk", "helpdesk", "sap", "oracle ebs", "online system", "online portal",
            "e portal", "digital platform", "case management system", "queue management system", "devops",
            "software house*", "software firm*", "it firm*", "it compan*", "custom* software", "software application*",
            "api integration", "database development", "data cent* solution", "it system*", "ict solution*",
            "ict infrastructure", "ict services", "document management system", "dms", "e procurement", "e filing",
            "e ticketing", "hospital management", "school management system", "land record*", "computeri*ation",
            "it hardware and software", "application support", "software support", "software maintenance",
            "it managed services", "it outsourc*", "technology partner*", "digital solution*", "smart solution*",
            "tracking system", "monitoring and evaluation system", "online application system", "it enabled",
            "?software", "?application*", "?portal", "?platform", "?system*", "?implementation", "?integration",
            "?consultan*", "?digital", "?automation", "?website", "?database", "?module*",
        ],
        "title_only": ["sap"], "block": ["civil", "hr"],
        "not": {"e office": "s e office|rehabilitation|road|xen", "helpdesk": "logo", "mis": "miscellaneous|mis c", "sap": "sapling", "emis": "emission", "dms": "dms school",
                "digitiz*": "digitizer", "it support": "", "tracking system": "solar tracking",
                "e ticketing": "sms|circuit|dplc|leased|bandwidth"},
    },
    "hw": {
        "mode": "partner",
        "terms": [
            "desktop machine*", "all in one desktop*", "aio desktop*", "enterprise hardware", "dell emc", "projection system*", "ar vr lab*", "vr lab*", "managed print*", "computer and it equipment",
            "laptop*", "desktop computer*", "desktop pc*", "desktops", "personal computer*", "computers",
            "computer system*", "computer hardware", "computer equipment", "it equipment", "ict equipment",
            "it hardware", "rack server*", "rack mount server*", "blade server*", "gpu server*", "servers",
            "server hardware", "san storage", "nas storage", "network attached storage", "storage area network",
            "storage system*", "storage solution*", "hyper converged", "hyperconverged", "hci", "workstation*",
            "thin client*", "chromebook*", "tablet pc*", "tablets", "ipad*", "all in one pc*", "multimedia projector*",
            "smart board*", "interactive board*", "interactive display*", "led display*", "smd screen*", "video wall*",
            "printers", "scanners", "network printer*", "computer lab*", "it lab", "ups system*", "online ups",
            "it peripheral*", "computer accessor*", "it accessor*", "it items", "it goods", "computer items",
            "digital signage", "kiosk*",
            "?computer*", "?server*", "?storage", "?printer*", "?scanner*", "?desktop*", "?hardware", "?ups", "?tablet*",
            "?projector*", "?monitor*", "?lcd*", "?led*",
        ],
        "block": ["health"],
        "not": {"tablets": "mg|medicine|drug|syrup|capsule|injection|vitamin", "servers": "food|waiter",
                "scanners": "baggage|x ray|body|metal|ultrasound|ct scan", "kiosk*": "tuck|food|canteen|construction",
                "storage system*": "fuel|water|oil|battery|energy|cold|grain", "storage solution*": "fuel|water|oil|battery|energy|cold|grain",
                "computers": "stationery|flow computer", "workstation*": "furniture|wooden|chair|table"},
    },
    "qai": {
        "mode": "own",
        "terms": [
            "discourse analysis",
            "artificial intelligence", "ai based", "ai enabled", "ai powered", "ai driven", "ai solution*",
            "ai platform", "ai system*", "ai model*", "generative ai", "machine learning", "data analytics",
            "analytics", "big data", "data science", "business intelligence", "data warehouse", "data lake",
            "gis mapping", "gis based", "gis system", "gis software", "gis survey", "gis lab",
            "geographic information system", "geographical information system", "geospatial", "geo spatial",
            "predictive", "computer vision", "video analytics", "natural language", "nlp", "data platform",
            "power bi", "tableau", "qlik", "credit scoring", "data visuali*", "dashboard development",
            "data driven", "data mining", "llm", "large language model*", "ai agent*", "ai assistant*",
            "command and control dashboard", "decision support system",
            "?ai", "?gis", "?dashboard*", "?data", "?insight*", "?analysis",
        ],
        "not": {"analytics": "", "predictive": "predictive maintenance of (plant|turbine|machine)"},
    },
    "qmsg": {
        "mode": "own",
        "terms": [
            "bulk sms", "sms service*", "sms gateway", "sms alert*", "sms solution*", "sms platform", "short code*",
            "sms", "a2p", "ussd", "voice broadcast*", "robocall*", "robo call*", "outbound dialing", "obd",
            "voice message*", "text message*", "sms based", "otp service*", "otp", "notification service*",
            "bulk messaging", "messaging service*", "messaging platform", "sms notification*", "branded sms",
            "transactional sms", "transaction sms", "masking", "sms api",
            "?messaging", "?alert*", "?notification*",
        ],
        "not": {"sms": "sales meter|ssgc|sngpl|sui |safety management|school management|gas|pressure|regulat|cps |tbs ",
                "obd": "scanner|diagnostic|vehicle", "otp": "outpatient|therapeutic", "masking": "tape|paint",
                "short code*": "building code"},
    },
    "omni": {
        "mode": "own",
        "terms": [
            "whatsapp", "omnichannel", "omni channel", "cpaas", "chatbot*", "chat bot*", "citizen engagement",
            "complaint management", "complaint cell", "grievance redress*", "customer engagement", "crm",
            "customer relationship management", "live chat", "conversational", "citizen feedback",
            "feedback system", "feedback management", "customer experience", "contact cent* solution",
            "complaint portal", "complaint handling", "ticketing system", "customer support platform",
            "citizen contact cent*", "customer care",
            "?complaint*", "?grievance*", "?feedback", "?engagement", "?campaign*",
        ],
        "not": {"conversational": "english|language course", "grievance redress*": "committee|grc"},
    },
    "qmkt": {
        "mode": "own",
        "terms": [
            "awareness campaign*", "media campaign*", "digital marketing", "social media marketing",
            "social media campaign*", "social media management", "advertising agenc*", "advertisement agenc*",
            "advertising campaign*", "digital advertising", "sms marketing", "behaviour change communication",
            "behavior change communication", "mass awareness", "public awareness", "communication campaign*",
            "digital media campaign*", "outreach campaign*", "digital media", "media buying", "advertising services",
            "marketing services", "marketing agenc*", "brand activation", "publicity campaign*", "digital campaign*",
            "communication strategy", "digital outreach", "influencer*",
            "?awareness", "?advertis*", "?marketing", "?campaign*", "?outreach", "?publicity", "?branding",
        ],
        "not": {"advertising agenc*": "", "public awareness": "", "communication strategy": ""},
    },
    "cm2m": {
        "mode": "own",
        "terms": [
            "m2m", "machine to machine", "m2m sim*", "iot sim*", "telemetry", "private apn", "apn", "static ip sim*",
            "gprs", "gprs modem*", "gsm modem*", "amr meter*", "amr system*", "ami", "automatic meter reading",
            "advanced metering infrastructure", "smart meter* communication", "metering communication",
            "data sims for", "sim based", "gsm based", "gprs based", "4g modem*", "lte modem*", "cellular modem*",
            "?amr", "?modem*", "?meter*", "?metering",
        ],
        "block": ["health"],
        "not": {"ami": "amikacin|amino", "apn": "apnea", "telemetry": "cardiac|patient|ecg|bed|icu"},
    },
    "qiot": {
        "mode": "own",
        "terms": [
            "production monitoring system",
            "iot", "internet of things", "lorawan", "lora", "nb iot", "sensor network*", "iot platform", "iot based",
            "smart sensor*", "remote monitoring", "environmental monitoring system", "energy monitoring",
            "energy management system", "smart meter*", "smart metering", "scada", "telemetry system*",
            "water level monitoring", "smart agriculture", "device management platform", "smart water", "smart grid",
            "early warning system*", "real time monitoring", "automatic weather station*", "aws station*",
            "flood early warning", "smart irrigation", "condition monitoring", "asset performance management",
            "smart building", "industrial iot", "iiot", "digital twin*", "remote terminal unit*", "rtu", "data logger*",
            "?sensor*", "?monitoring system*", "?smart", "?automation", "?weather",
        ],
        "block": ["health"],
        "not": {"lora": "loralai|flora", "remote monitoring": "patient|cardiac|icu", "condition monitoring": "patient"},
    },
    "iots": {
        "mode": "own",
        "terms": [
            "surveillance equipment",
            "vehicle tracking", "fleet tracking", "fleet management", "tracker*", "tracking device*", "gps tracking",
            "gps tracker*", "vehicle tracker*", "vehicle tracking system", "fuel monitoring", "fuel management system",
            "asset tracking", "cctv", "surveillance system*", "surveillance camera*", "video surveillance",
            "security surveillance", "ip camera*", "security camera*", "cc tv", "anpr", "number plate recognition",
            "e challan", "traffic management system", "intelligent traffic", "smart parking", "parking management",
            "push to talk", "ptt", "cold chain monitoring", "air quality monitoring", "water quality monitoring",
            "smart street light*", "street light management", "building automation", "building management system",
            "bms", "biometric attendance", "biometric device*", "biometric system*", "biometric machine*",
            "access control system*", "smart city", "safe city", "command and control cent*",
            "command and control system", "body worn camera*", "face recognition", "facial recognition",
            "attendance system", "attendance machine*", "nvr", "dvr", "walkie talkie*", "two way radio*",
            "smart classroom*", "intelligent transport", "its", "vms", "video management", "drone surveillance", "surveillance drone*", "drone survey", "drone based",
            "gps device*", "speed camera*", "weigh in motion", "electronic toll", "smart card*", "rfid",
            "?camera*", "?surveillance", "?tracking", "?biometric*", "?access control", "?parking", "?traffic", "?gps", "?drone*", "?uav",
        ],
        "block": ["health"],
        "not": {"tracker*": "solar", "bms": "battery management|bms college|bms degree", "its": "its own|and its|of its|for its|with its|in its|to its|its ",
                "vms": "vaccine", "ptt": "ptt test|partial thromboplastin", "dvr": "", "smart card*": "printing|driving licen",
                "rfid": ""},
    },
    "sme": {
        "mode": "own",
        "terms": [
            "mobile device management", "mdm", "field force", "workforce management", "digital invoic*",
            "e invoic*", "pos software", "point of sale software", "field data collection", "field monitoring app*",
            "attendance app*", "field staff monitoring", "mobile workforce", "inventory management system",
            "hr and payroll software", "payroll software", "accounting software", "fleet app*", "geo tagging",
            "geo fencing", "geofencing",
            "?workforce", "?field staff", "?erp", "?crm", "?workflow", "?invoic*",
        ],
        "not": {"mdm": "mdm ma"},
    },

    # ───────────────────────────── FINANCIAL SERVICES ─────────────────────────────
    "jccol": {
        "mode": "own",
        "terms": [
            "fee collection", "collection of fee*", "challan collection", "collection of challan*", "tax collection",
            "collection of tax*", "revenue collection", "collection of revenue", "bill collection",
            "collection of bill*", "utility bill collection", "payment collection", "collection service*",
            "collection agent*", "collection bank*", "p2g", "government payment*", "online fee", "online collection",
            "digital collection", "cash collection", "bill payment*", "collection of dues", "toll collection",
            "online payment of fee*", "payment of challan*", "digital payment solution*", "branchless banking",
            "mobile wallet*", "mobile banking", "mobile money", "digital wallet*", "e wallet*", "jazzcash",
            "easypaisa", "raast", "over the counter collection", "otc collection", "e ticketing", "online ticketing",
            "fare collection", "fine collection", "collection of fine*", "collection of toll", "collection account*",
            "electronic money", "emi licen*", "payment service*",
            "?collection*", "?challan*", "?fee", "?fees", "?payment*", "?wallet*", "?ticketing",
        ],
        "block": ["health", "waste"],
        "not": {"e ticketing": "sms|circuit|dplc|leased|bandwidth", "collection service*": "garbage|waste|sample|blood|data|milk|specimen|refuse|debris|scrap",
                "cash collection": "garbage|waste", "raast": "", "payment service*": "",
                "tax collection": "advisor|consultant for"},
    },
    "jcg2p": {
        "mode": "own",
        "terms": [
            "disbursement*", "cash transfer*", "g2p", "stipend*", "salary disbursement", "payroll disbursement",
            "payment of stipend*", "subsidy disbursement", "cash grant*", "beneficiary payment*",
            "social protection payment*", "zakat disbursement", "wage disbursement", "payment service provider*",
            "financial service provider*", "cash assistance", "relief payment*", "digital disbursement",
            "disbursement partner*", "disbursement agent*", "payment partner*", "bulk payment*", "bulk disbursement",
            "payment to beneficiar*", "conditional cash", "unconditional cash", "payment agenc*",
            "?subsid*", "?welfare", "?beneficiar*", "?income support", "?payroll", "?salary", "?zakat",
        ],
        "not": {"disbursement*": "disbursement linked|loan disbursement officer|adb loan|loan no|credit no|financing", "stipend*": ""},
    },
    "jcpg": {
        "mode": "own",
        "terms": [
            "payment gateway*", "online payment*", "e payment*", "epayment*", "card payment*", "internet payment",
            "payment integration", "payment processing", "payment aggregator*", "online payment system",
            "payment solution*", "payment platform*", "payment system*", "digital payment gateway",
            "internet payment gateway", "ipg", "merchant payment*", "online fee payment",
            "?gateway", "?checkout", "?payment*",
        ],
        "not": {"payment system*": "", "ipg": "ipg generator"},
    },
    "jcqr": {
        "mode": "own",
        "terms": [
            "qr code payment*", "qr payment*", "raast qr", "qr based payment*", "pos machine*", "pos terminal*",
            "point of sale terminal*", "card machine*", "cashless", "merchant acquiring", "merchant onboarding",
            "tap to pay", "tap on phone", "digital payment*", "payment terminal*", "pos device*", "soft pos",
            "merchant qr", "digital payments", "payment acceptance",
            "?qr", "?merchant*", "?pos", "?till", "?parking",
        ],
    },
    "jcmore": {
        "mode": "own",
        "terms": [
            "debit card*", "prepaid card*", "paypak", "payroll card*", "co branded card*", "nano loan*", "bnpl",
            "buy now pay later", "virtual card*", "atm card*", "salary card*", "benefit card*", "ration card*",
            "?savings", "?card*",
        ],
        "not": {"prepaid card*": "printing|scratch", "ration card*": "printing"},
    },
    "mmbl": {
        "mode": "own",
        "terms": [
            "microfinance", "micro finance", "microcredit", "micro credit", "interest free loan*", "loan scheme*",
            "loan programme", "loan program", "financing scheme*", "sme financing", "msme financ*", "sme loan*",
            "women entrepreneur*", "youth loan*", "financial inclusion", "credit line*", "partner bank*",
            "lending partner*", "loan disbursement", "e bike financing", "housing finance", "low cost housing finance",
            "kamyab jawan", "youth business loan*", "executing agenc* for loan*", "partner financial institution*",
            "participating financial institution*", "microfinance bank*", "microfinance institution*", "qarz",
            "revolving fund", "credit facility", "running finance", "term finance", "financing facility",
            "?loan*", "?credit", "?financ*", "?entrepreneur*", "?msme", "?sme", "?freelanc*",
        ],
        "not": {"credit facility": "", "running finance": "", "financing facility": ""},
    },
    "mmagri": {
        "mode": "own",
        "terms": [
            "agri* loan*", "agricultur* financ*", "agri financ*", "agricultur* credit", "agri credit",
            "kissan card*", "kisan card*", "farmer* loan*", "crop loan*", "livestock loan*", "livestock financ*",
            "tractor scheme", "tractor financ*", "solar financ*", "solarization financ*", "kissan package",
            "kisan package", "agri* lending", "farm mechani*ation financ*", "green tractor", "tube well solari*ation financ*",
            "warehouse receipt financ*", "farmer financ*", "kissan dost",
            "?agri*", "?farmer*", "?livestock", "?tractor*", "?kissan", "?kisan", "?crop*", "?solar", "?dairy",
        ],
    },
    "mmdep": {
        "mode": "own",
        "terms": [
            "bank account opening", "account opening", "banking service*", "banking facilit*", "salary account*",
            "pension disbursement", "pension payment*", "term deposit*", "placement of funds", "placement of surplus",
            "investment of surplus funds", "investment of funds", "deposit of funds", "tdr", "tdrs",
            "designated bank*", "selection of bank*", "hiring of bank*", "empanelment of bank*", "panel of bank*",
            "cash management service*", "bank for", "banks for", "profit rate*", "rate of return on deposit*",
            "short term investment", "investment of provident fund", "pls account*", "daily product account*",
            "bid* from bank*", "quotation* from bank*", "proposal* from bank*", "scheduled bank*", "commercial bank*",
            "?bank", "?banks", "?banking", "?deposit*", "?pension*", "?account*", "?treasury", "?investment",
        ],
        "not": {"tdr": "tdr meter|time domain|usf", "tdrs": "usf", "banking service*": "banking services corporation|sbp bsc|bsc bank", "bank for": "blood|data|power|world bank|seed|food",
                "banks for": "blood|power|data|seed|food", "commercial bank*": "", "scheduled bank*": ""},
        "block": ["health"],
    },
    "ins": {
        "mode": "own",
        "terms": [
            "health insurance", "group health insurance", "group life insurance", "life insurance", "takaful",
            "micro insurance", "medical insurance", "hospitali*ation cover*", "health cover*", "accidental insurance",
            "group insurance", "employee* insurance", "group health", "group life", "group term life",
            "health and life insurance", "life and health insurance", "medical cover*", "opd cover*",
            "family takaful", "health takaful", "insurance of employees", "staff insurance", "group medical",
            "?insurance", "?hospitali*", "?medical", "?health",
        ],
        "not": {"life insurance": "life insurance corporation|valuation", "takaful": "takaful division|printing"},
    },
    "jsure": {
        "mode": "own",
        "terms": [
            "insurance", "reinsurance", "insurance coverage", "insurance services", "insurance of vehicle*",
            "vehicle* insurance", "motor insurance", "fire insurance", "property insurance", "marine insurance",
            "comprehensive insurance", "asset* insurance", "insurance of asset*", "crop insurance",
            "livestock insurance", "cyber insurance", "cyber and digital insurance", "engineering insurance",
            "insurance policy", "insurance policies", "insurance compan*", "general insurance", "insurance cover*",
            "cash in transit insurance", "fidelity insurance", "aviation insurance", "hull insurance",
            "third party liability insurance", "contractor all risk", "erection all risk", "index insurance",
            "area yield", "insurance broker*", "general takaful", "insurers", "insurer", "insurance arrangement*",
            "?insur*", "?coverage", "?liability", "?premium",
        ],
        "title_only": ["insurance", "reinsurance", "insurers", "insurer"],
        "not": {"insurance": "including insurance|freight and insurance|cost insurance|insurance and freight|cif|with insurance|inclusive of insurance|insurance corporation|valuation"},
    },

    # ───────────────────────────── DIGITAL PLATFORMS ─────────────────────────────
    "tam": {
        "mode": "own",
        "terms": [
            "video streaming", "live streaming", "ott", "digital content", "content platform", "streaming platform",
            "video on demand", "webcast*", "streaming service*", "content hub", "digital content hub",
            "video content", "content production", "digital broadcast*", "live broadcast*", "online streaming",
            "?video*", "?content", "?media", "?streaming", "?broadcast*",
        ],
        "not": {"ott": "otter|ottoman"},
    },
    "sim": {
        "mode": "own",
        "terms": [
            "citizen portal", "citizen app*", "citizen facilitation app*", "super app", "self service portal",
            "self care app*", "e kyc", "ekyc", "digital onboarding", "digital identity", "digital id",
            "citizen services app*", "e services portal", "one window portal", "citizen service portal",
            "citizen mobile app*", "self service kiosk*", "customer onboarding", "customer app*", "consumer app*",
            "?self service", "?identity", "?onboarding", "?kyc", "?citizen*",
        ],
    },
    "gn": {
        "mode": "own",
        "terms": [
            "gamif*", "e learning", "elearning", "learning management system", "lms", "online learning platform",
            "digital learning", "online training platform", "edtech", "game based learning", "esports", "e sports",
            "online course*", "digital literacy", "digital skills", "online learning", "virtual learning",
            "learning platform", "learning portal", "mooc*", "blended learning",
            "?training", "?learning", "?skills", "?bootcamp*", "?students", "?courses",
        ],
        "not": {"lms": "lms tower"},
    },
}

# Context patterns. A context is "on" for a tender when the pattern is found in its title.
# Products list the contexts that switch off their SUPPORT terms and make the match "context risk".
CONTEXTS = {
    "power": r"\d+ ?kv|\bkv\b|kva|grid station|transmission line|switchgear|transformer|feeder|ht lt|lt ht|conductor|pylon|distribution line|electrification|circuit breaker|panel board|\bht\b|\blt\b|sub station|substation|power cable|energy meter|pole |poles ",
    "civil": r"construction of|renovation|rehabilitation of|civil work|boundary wall|sewer|drain|pcc|tuff tile|flooring|masonry|excavation|carpeting|white ?wash|paint work|repair of (road|building|office|residence|quarter|bungalow|roof|washroom)|re routing|rerouting|shifting of|laying of|trench|manhole|retaining wall|shed|plumbing",
    "health": r"medicine|surgical|drug|injection|syrup|reagent|vaccine|dental|pharma|laboratory chemical|\bniv\b|medical equipment|hospital equipment|patient|diagnostic|x ray|disposable|implant|dialysis|\bmg\b|capsule",
    "gas": r"ssgc|sngpl|sui northern|sui southern|gas pipeline|gas main|\btbs\b|\bcms\b|sales meter|gas network|distribution network|pipeline network",
    "water": r"water supply|sewerage|drainage|irrigation network|canal|road network|rail network",
    "waste": r"garbage|solid waste|refuse|sample collection|blood|specimen|milk|debris",
    "hr": r"security guard|janitorial|outsourcing of (human resource|manpower|staff|security)|hiring of (staff|manpower|labou?r|drivers?)|supply of manpower|manpower services",
}

# Tenders that are not company bids at all. Checked on the title.
EXCLUDE_TITLE = {
    "disposal": r"^(open )?auction|auction of|disposal of|sale of (old|used|unserviceable|condemned|scrap)|scrap|condemned|unserviceable|obsolete",
    "individual": r"hiring of (an? )?(individual )?(consultant|specialist|expert|officer|coordinator|advisor|adviser|manager|engineer|assistant|associate|analyst|developer|programmer)s?( \(|$| for | on | at | - )(?!.*\b(firm|company|agency|services|consultancy services)\b)|individual consultant",
    "property": r"hiring of (office|residential|rented) (building|accommodation|space)|purchase of (land|plot)|lease of (shop|land|building|canteen)|rent of (shop|building)|valuation of|renting range",
    # Supplies JazzWorld does not sell, even when the title names a digital system they are used in.
    "consumables": r"^(?!.*\b(it equipments?|it items|it goods|computer items|computer equipments?|computer hardware|hardware|software|laptops?|switch(es)?|ip phones?|data cent\w*|datacent\w*|cctv|nvr|servers?|network\w*|video conferencing)\b).*(\b(thermal|paper|printer|receipt|ticket|till) (paper )?rolls?\b|^printing (of|and)|printing of (policy|file|forms?|books?|calendars?|diar|brochure|leaflet|card)|\bstationery\b|\bstationary\b|\btoners?\b|\btonners?\b|\bcartridges?\b|\bconsumables\b)",
    # Firms hired to manage or monitor someone else's programme are not buying the programme's products.
    "oversight": r"(management|monitoring|consultancy|consulting) firm for (the )?(project management|monitoring|third party)|project management and monitoring of|third party (validation|verification|monitoring|evaluation)",
}

# Scope areas JazzWorld cannot deliver alone. First match per category.
PARTNER_GAPS = [
    ("civil", "Civil works, HVAC or power", r"hvac|civil work|construction|site build|air condition|electrification|raised floor|fire suppression|generator|precision cooling"),
    ("devices", "Device OEM or authorised distributor", r"laptop|desktop|computer|it equipment|ict equipment|it hardware|server|storage|printer|scanner|tablet|projector|ups|smart board|display|chromebook|workstation|mifi device|handset"),
    ("network", "Network OEM (Cisco, Huawei, Juniper)", r"cisco|juniper|aruba|huawei|core switch|network switch|router|access point|network equipment|networking equipment"),
    ("fortinet", "Security OEM authorisation", r"fortinet|fortigate|forti|palo alto|sophos|kaspersky|trend micro|crowdstrike|firewall|siem|edr|nessus"),
    ("microsoft", "Microsoft licensing", r"microsoft|office 365|m365|windows server|sql server|sharepoint|exchange online"),
    ("oracle", "Oracle authorisation", r"oracle"),
    ("vmware", "VMware authorisation", r"vmware"),
    ("linux", "Linux vendor authorisation", r"red hat|suse|linux"),
    ("software", "Software developer or system integrator", r"software development|application development|web portal|portal development|mobile app|erp|management information system|website development|web application|sap|digiti[sz]ation|automation of|information system|document management|e office"),
    ("iot", "IoT device or platform partner", r"cctv|camera|tracker|tracking device|sensor|smart meter|energy meter|ami meter|biometric|scada|rfid|drone|weather station|anpr|access control"),
    ("radio", "Radio or microwave OEM", r"radio link|microwave|ism band|vhf|uhf|walkie|satellite|vsat"),
    ("telephony", "Telephony OEM (Avaya, Cisco)", r"avaya|pabx|ip pbx|telephone exchange|ip phone"),
    ("reinsurance", "Reinsurance or co-insurance panel", r"reinsurance|aviation|hull|marine|co insurance"),
    ("content", "Content or training delivery partner", r"content production|training partner|studio|curriculum"),
]
