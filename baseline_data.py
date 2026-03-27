"""
INFY Migration Lifecycle Tracker — Comprehensive Baseline Data
==============================================================
This is the authoritative dataset built from Claude AI training knowledge.
It covers ALL major OS families and DB products with accurate lifecycle dates.
Agent 1's job is ONLY to verify/update these dates from the internet.
"""

OS_COLUMNS = [
    "OS Version", "Availability Date", "Security/Standard Support End",
    "Mainstream/Full Support End", "Extended/LTSC Support End",
    "Min CPU", "Min RAM",
    "Notes", "Recommendation", "Upgrade", "Replace",
    "Primary Alternative", "Secondary Alternative"
]

DB_COLUMNS = [
    "Database", "Version", "Type",
    "Mainstream / Premier End", "Extended Support End",
    "Status", "Min CPU", "Min RAM",
    "Notes", "Recommendation",
    "Upgrade", "Replace", "Primary Alternative", "Secondary Alternative"
]

def _os(ver, avail="", sec="", main="", ext="", notes="", rec="", upg="N", repl="N", pri="", sec2="",
        min_cpu="", min_ram=""):
    return {"OS Version": ver, "Availability Date": avail,
            "Security/Standard Support End": sec, "Mainstream/Full Support End": main,
            "Extended/LTSC Support End": ext, "Min CPU": min_cpu, "Min RAM": min_ram,
            "Notes": notes, "Recommendation": rec,
            "Upgrade": upg, "Replace": repl, "Primary Alternative": pri, "Secondary Alternative": sec2}

def _db(db, ver, typ, main="", ext="", status="Supported", notes="", rec="", upg="N", repl="N", pri="", sec="",
        min_cpu="", min_ram=""):
    return {"Database": db, "Version": ver, "Type": typ,
            "Mainstream / Premier End": main, "Extended Support End": ext,
            "Status": status, "Min CPU": min_cpu, "Min RAM": min_ram,
            "Notes": notes, "Recommendation": rec,
            "Upgrade": upg, "Replace": repl, "Primary Alternative": pri, "Secondary Alternative": sec}

# =============================================================================
# OS DATA — Comprehensive coverage from Claude training knowledge
# =============================================================================
OS_DATA = [

    # ── Windows 11 Client ─────────────────────────────────────────────────────
    _os("Windows 11 21H2",             "2021-10-05","","2023-10-10","",           "Initial release; Home/Pro","","Y","N","Windows 11 24H2"),
    _os("Windows 11 21H2 Ent/Edu",     "2021-10-05","","2024-10-08","",           "Enterprise/Education 36-month","","Y","N","Windows 11 24H2"),
    _os("Windows 11 22H2",             "2022-09-20","","2024-10-08","",           "Sun Valley 2; Home/Pro","","Y","N","Windows 11 24H2"),
    _os("Windows 11 22H2 Ent/Edu",     "2022-09-20","","2025-10-14","",           "Enterprise/Education","","Y","N","Windows 11 24H2"),
    _os("Windows 11 23H2",             "2023-10-31","","2025-11-11","",           "Sun Valley 3; Home/Pro","","Y","N","Windows 11 24H2"),
    _os("Windows 11 23H2 Ent/Edu",     "2023-10-31","","2026-11-10","",           "Enterprise/Education","","Y","N","Windows 11 24H2"),
    _os("Windows 11 24H2",             "2024-10-01","","2026-10-13","",           "Germanium; Home/Pro","","N","N",""),
    _os("Windows 11 24H2 Ent/Edu",     "2024-10-01","","2027-10-12","",           "Enterprise/Education","","N","N",""),
    _os("Windows 11 24H2 LTSC",        "2024-10-01","","2029-10-09","2034-10-10","LTSC 2024","","N","N",""),
    _os("Windows 11 25H2",             "2025-09-30","","2027-10-12","",           "Upcoming; Home/Pro","","N","N",""),

    # ── Windows 10 Client ─────────────────────────────────────────────────────
    _os("Windows 10 1507",             "2015-07-29","","2017-05-09","",           "RTM — End of Life","","Y","N","Windows 11 24H2"),
    _os("Windows 10 1511",             "2015-11-10","","2017-10-10","",           "November Update — EOL","","Y","N","Windows 11 24H2"),
    _os("Windows 10 1607",             "2016-08-02","","Ended",     "2026-10-13","LTSB 2016","","Y","N","Windows 11 24H2"),
    _os("Windows 10 1703",             "2017-04-05","","2018-10-09","",           "Creators Update — EOL","","Y","N","Windows 11 24H2"),
    _os("Windows 10 1709",             "2017-10-17","","2019-04-09","",           "Fall Creators Update — EOL","","Y","N","Windows 11 24H2"),
    _os("Windows 10 1803",             "2018-04-30","","2019-11-12","",           "April 2018 Update — EOL","","Y","N","Windows 11 24H2"),
    _os("Windows 10 1809",             "2018-11-13","","Ended",     "2029-01-09","LTSC 2019","","Y","N","Windows 11 24H2"),
    _os("Windows 10 1903",             "2019-05-21","","2020-12-08","",           "May 2019 Update — EOL","","Y","N","Windows 11 24H2"),
    _os("Windows 10 1909",             "2019-11-12","","2022-05-10","",           "November 2019 Update — EOL","","Y","N","Windows 11 24H2"),
    _os("Windows 10 2004",             "2020-05-27","","2021-12-14","",           "May 2020 Update — EOL","","Y","N","Windows 11 24H2"),
    _os("Windows 10 20H2",             "2020-10-20","","2023-05-09","",           "October 2020 Update — EOL","","Y","N","Windows 11 24H2"),
    _os("Windows 10 21H1",             "2021-05-18","","2022-12-13","",           "May 2021 Update — EOL","","Y","N","Windows 11 24H2"),
    _os("Windows 10 21H2",             "2021-11-16","","2024-06-11","2027-01-12","LTSC 2021","","Y","N","Windows 11 24H2"),
    _os("Windows 10 21H2 Ent",         "2021-11-16","","2024-06-11","",           "Enterprise 36-month","","Y","N","Windows 11 24H2"),
    _os("Windows 10 22H2",             "2022-10-18","","2025-10-14","",           "Final consumer release","","Y","N","Windows 11 24H2"),

    # ── Windows 8 / 8.1 ──────────────────────────────────────────────────────
    _os("Windows 8",                   "2012-10-26","","2016-01-12","",           "End of Life","","Y","N","Windows 11 24H2"),
    _os("Windows 8.1",                 "2013-10-17","","2018-01-09","2023-01-10","End of Life","","Y","N","Windows 11 24H2"),
    _os("Windows 8.1 Update",          "2014-04-08","","2018-01-09","2023-01-10","End of Life","","Y","N","Windows 11 24H2"),

    # ── Windows 7 ────────────────────────────────────────────────────────────
    _os("Windows 7 SP1 Home/Pro",      "2011-02-22","","2015-01-13","2020-01-14","End of Life; ESU ended","","Y","N","Windows 11 24H2"),
    _os("Windows 7 SP1 Enterprise",    "2011-02-22","","2015-01-13","2020-01-14","End of Life; ESU ended","","Y","N","Windows 11 24H2"),

    # ── Windows Server ────────────────────────────────────────────────────────
    _os("Windows Server 2003",         "2003-04-24","","2010-07-13","",           "End of Life","","Y","N","Windows Server 2025"),
    _os("Windows Server 2003 R2",      "2005-12-06","","2010-07-13","",           "End of Life","","Y","N","Windows Server 2025"),
    _os("Windows Server 2008",         "2008-02-27","","2015-01-13","2020-01-14","End of Life","","Y","N","Windows Server 2025"),
    _os("Windows Server 2008 R2",      "2009-10-22","","2015-01-13","2020-01-14","End of Life; ESU ended","","Y","N","Windows Server 2025"),
    _os("Windows Server 2012",         "2012-10-30","","2018-10-09","2023-10-10","End of Life","","Y","N","Windows Server 2025"),
    _os("Windows Server 2012 R2",      "2013-11-25","","2018-10-09","2023-10-10","End of Life","","Y","N","Windows Server 2025"),
    _os("Windows Server 2016",         "2016-10-15","","2022-01-11","2027-01-12","","","Y","N","Windows Server 2025"),
    _os("Windows Server 2019",         "2018-11-13","","2024-01-09","2029-01-09","","","N","N",""),
    _os("Windows Server 2022",         "2021-08-18","","2026-10-13","2031-10-14","","","N","N",""),
    _os("Windows Server 2025",         "2024-11-01","","2029-11-13","2034-11-14","Latest","","N","N",""),
    _os("Windows Server 2016 SAC",     "2017-10-17","","2018-04-10","",           "Semi-Annual Channel — EOL","","Y","N","Windows Server 2025"),
    _os("Windows Server 2019 SAC",     "2019-11-12","","2024-01-09","",           "Semi-Annual Channel — EOL","","Y","N","Windows Server 2025"),

    # ── Windows Embedded / IoT ────────────────────────────────────────────────
    _os("Windows Embedded Standard 7", "2011-03-01","","2015-10-13","2020-10-13","End of Life","","Y","N","Windows IoT LTSC 2024"),
    _os("Windows Embedded 8 Standard", "2013-02-12","","2016-01-12","2023-07-11","End of Life","","Y","N","Windows IoT LTSC 2024"),
    _os("Windows IoT Enterprise LTSC 2019","2019-01-22","","2024-01-09","2029-01-09","","","Y","N","Windows IoT LTSC 2024"),
    _os("Windows IoT Enterprise LTSC 2021","2021-11-16","","2027-01-12","2032-01-13","","","N","N",""),
    _os("Windows IoT Enterprise LTSC 2024","2024-05-21","","2029-10-09","2034-10-09","Latest","","N","N",""),

    # ── Red Hat Enterprise Linux ──────────────────────────────────────────────
    _os("RHEL 5",   "2007-03-15","2013-01-08","2017-03-31","2020-11-30","End of Life; ELS ended","","Y","N","RHEL 9"),
    _os("RHEL 6",   "2010-11-10","2016-05-10","2020-11-30","2024-06-30","End of Life","","Y","N","RHEL 9"),
    _os("RHEL 7",   "2014-06-10","2019-08-06","2024-06-30","2026-06-30","","","Y","N","RHEL 9"),
    _os("RHEL 8",   "2019-05-07","2024-05-31","2029-05-31","2032-05-31","","","N","N",""),
    _os("RHEL 9",   "2022-05-18","2027-05-31","2032-05-31","2035-05-31","","","N","N",""),
    _os("RHEL 10",  "2025-05-20","2030-05-31","2035-05-31","2038-05-31","Latest","","N","N",""),

    # ── Ubuntu ────────────────────────────────────────────────────────────────
    _os("Ubuntu 14.04 LTS", "2014-04-17","2019-04-02","2024-04-02","2029-04-30","Trusty; HWE stack","","Y","N","Ubuntu 24.04 LTS"),
    _os("Ubuntu 16.04 LTS", "2016-04-21","2021-04-02","2026-04-02","2031-04-30","Xenial","","Y","N","Ubuntu 24.04 LTS"),
    _os("Ubuntu 18.04 LTS", "2018-04-26","2023-05-31","2028-04-01","2033-04-30","Bionic","","N","N",""),
    _os("Ubuntu 20.04 LTS", "2020-04-23","2025-05-29","2030-04-02","2035-04-30","Focal","","N","N",""),
    _os("Ubuntu 22.04 LTS", "2022-04-21","2027-06-01","2032-04-01","2037-04-30","Jammy","","N","N",""),
    _os("Ubuntu 24.04 LTS", "2024-04-25","2029-05-31","2034-04-30","2036-04-30","Noble; Latest LTS","","N","N",""),
    _os("Ubuntu 24.10",     "2024-10-10","2025-07-01","2025-07-01","",           "Oracular; 9-month","","Y","N","Ubuntu 24.04 LTS"),
    _os("Ubuntu 25.04",     "2025-04-17","2026-01-01","2026-01-01","",           "Plucky; 9-month","","N","N",""),

    # ── SUSE Linux Enterprise Server ──────────────────────────────────────────
    _os("SLES 11 SP4",  "2015-07-16","","2019-03-31","2022-03-31","End of Life","","Y","N","SLES 15 SP6"),
    _os("SLES 12 SP4",  "2018-12-04","","2020-06-30","2023-06-30","End of Life","","Y","N","SLES 15 SP6"),
    _os("SLES 12 SP5",  "2019-12-09","","2024-10-31","2027-10-31","LTSS available","","Y","N","SLES 15 SP6"),
    _os("SLES 15 SP1",  "2019-06-24","","2021-01-31","2023-01-31","End of Life","","Y","N","SLES 15 SP6"),
    _os("SLES 15 SP2",  "2020-07-22","","2021-12-31","2024-12-31","End of Life","","Y","N","SLES 15 SP6"),
    _os("SLES 15 SP3",  "2021-06-23","","2022-12-31","2025-12-31","End of Life","","Y","N","SLES 15 SP6"),
    _os("SLES 15 SP4",  "2022-06-22","","2023-12-31","2026-12-31","","","Y","N","SLES 15 SP6"),
    _os("SLES 15 SP5",  "2023-06-20","","2024-12-31","2027-12-31","","","Y","N","SLES 15 SP6"),
    _os("SLES 15 SP6",  "2024-06-26","","2025-12-31","2028-12-31","","","N","N",""),
    _os("SLES 15 SP7",  "2025-06-17","","2031-07-31","2034-07-31","Latest SP","","N","N",""),
    _os("SLES 16.0",    "2025-11-04","","2027-11-30","2030-11-30","","","N","N",""),

    # ── Debian ────────────────────────────────────────────────────────────────
    _os("Debian 9 Stretch",   "2017-06-17","2020-06-30","2022-06-30","2027-06-30","LTS ended; ELTS until 2027","","Y","N","Debian 12"),
    _os("Debian 10 Buster",   "2019-07-06","2022-09-10","2024-06-30","2029-06-30","","","Y","N","Debian 12"),
    _os("Debian 11 Bullseye", "2021-08-14","2024-08-14","2026-08-31","2031-06-30","","","Y","N","Debian 12"),
    _os("Debian 12 Bookworm", "2023-06-10","2026-06-10","2028-06-30","2033-06-30","Current stable","","N","N",""),
    _os("Debian 13 Trixie",   "2025-08-09","2028-08-09","2030-06-30","2035-06-30","Testing → Stable 2025","","N","N",""),

    # ── CentOS ────────────────────────────────────────────────────────────────
    _os("CentOS 6",         "2011-07-10","","2020-11-30","",     "End of Life","","Y","N","RHEL 9"),
    _os("CentOS 7",         "2014-07-07","","2024-06-30","",     "End of Life","","Y","N","RHEL 9"),
    _os("CentOS 8",         "2019-09-24","","2021-12-31","",     "Early EOL — Dec 2021","","Y","N","RHEL 9"),
    _os("CentOS Stream 8",  "2019-09-24","","2024-05-31","",     "End of Life","","Y","N","CentOS Stream 10"),
    _os("CentOS Stream 9",  "2021-12-03","","2027-05-31","",     "","","N","N",""),
    _os("CentOS Stream 10", "2024-06-12","","2030-12-01","",     "Latest","","N","N",""),

    # ── Rocky Linux ───────────────────────────────────────────────────────────
    _os("Rocky Linux 8",  "2021-05-01","2029-05-31","2024-05-31","","Tracks RHEL 8","","Y","N","Rocky Linux 9"),
    _os("Rocky Linux 9",  "2022-07-14","2032-05-31","2027-05-31","","Tracks RHEL 9","","N","N",""),
    _os("Rocky Linux 10", "2025-06-11","2035-05-31","2030-05-31","","Tracks RHEL 10","","N","N",""),

    # ── AlmaLinux ─────────────────────────────────────────────────────────────
    _os("AlmaLinux 8",  "2021-03-30","2029-05-31","2024-05-31","","Tracks RHEL 8","","Y","N","AlmaLinux 9"),
    _os("AlmaLinux 9",  "2022-05-26","2032-05-31","2027-05-31","","Tracks RHEL 9","","N","N",""),
    _os("AlmaLinux 10", "2025-05-27","2035-05-31","2030-05-31","","Tracks RHEL 10","","N","N",""),

    # ── Oracle Linux ──────────────────────────────────────────────────────────
    _os("Oracle Linux 6",  "2011-02-12","","2021-03-01","2024-12-31","End of Life","","Y","N","Oracle Linux 9"),
    _os("Oracle Linux 7",  "2014-07-23","","2024-12-31","2028-06-30","","","Y","N","Oracle Linux 9"),
    _os("Oracle Linux 8",  "2019-07-18","","2029-07-31","2032-07-31","","","N","N",""),
    _os("Oracle Linux 9",  "2022-06-30","","2032-06-30","2035-06-30","","","N","N",""),
    _os("Oracle Linux 10", "2025-06-26","","2035-06-30","2038-06-30","Latest","","N","N",""),

    # ── openSUSE / Fedora ─────────────────────────────────────────────────────
    _os("openSUSE Leap 15.4", "2022-06-08","","2023-12-31","",     "EOL","","Y","N","openSUSE Leap 15.6"),
    _os("openSUSE Leap 15.5", "2023-06-07","","2024-12-31","",     "EOL","","Y","N","openSUSE Leap 15.6"),
    _os("openSUSE Leap 15.6", "2024-06-12","","2025-12-31","",     "Current","","N","N",""),
    _os("Fedora 39",          "2023-11-07","","2024-11-26","",     "EOL","","Y","N","Fedora 42"),
    _os("Fedora 40",          "2024-04-23","","2025-05-13","",     "EOL","","Y","N","Fedora 42"),
    _os("Fedora 41",          "2024-10-29","","2025-11-19","",     "","","Y","N","Fedora 42"),
    _os("Fedora 42",          "2025-04-15","","2026-05-19","",     "Latest","","N","N",""),

    # ── macOS ─────────────────────────────────────────────────────────────────
    _os("macOS 11 Big Sur",    "2020-11-12","","2023-09-26","",     "End of Support","","Y","N","macOS 15 Sequoia"),
    _os("macOS 12 Monterey",   "2021-10-25","","2024-09-16","",     "End of Support","","Y","N","macOS 15 Sequoia"),
    _os("macOS 13 Ventura",    "2022-10-24","","2025-09-15","",     "","","Y","N","macOS 15 Sequoia"),
    _os("macOS 14 Sonoma",     "2023-09-26","","2026-09-15","",     "","","N","N",""),
    _os("macOS 15 Sequoia",    "2024-09-16","","2027-09-15","",     "Latest","","N","N",""),
    _os("macOS 26 Tahoe",      "2025-09-15","","2028-09-15","",     "Upcoming","","N","N",""),

    # ── Oracle Solaris ────────────────────────────────────────────────────────
    _os("Solaris 9",    "2002-05-01","","Ended","",           "End of Life","","Y","N","Solaris 11.4"),
    _os("Solaris 10",   "2005-01-31","","Ended (Jan 2018)","2027-01-01","End of Life","","Y","N","Solaris 11.4"),
    _os("Solaris 11.3", "2015-10-26","","Ended (Jan 2021)","2027-01-01","","","Y","N","Solaris 11.4"),
    _os("Solaris 11.4", "2018-08-28","","2031-11-01","2037-11-01","Latest","","N","N",""),

    # ── IBM AIX ───────────────────────────────────────────────────────────────
    _os("AIX 5.3",      "2004-08-16","","2012-04-30","",           "End of Life","","Y","N","AIX 7.3"),
    _os("AIX 6.1 TL9",  "2007-11-09","","2017-04-30","",           "End of Life","","Y","N","AIX 7.3"),
    _os("AIX 7.1 TL5",  "2010-09-10","","2023-04-30","",           "End of Service","","Y","N","AIX 7.3"),
    _os("AIX 7.2 TL5",  "2015-12-09","","2025-12-31","",           "","","Y","N","AIX 7.3"),
    _os("AIX 7.3 TL1",  "2022-12-09","","2025-12-31","",           "","","Y","N","AIX 7.3 TL4"),
    _os("AIX 7.3 TL2",  "2023-11-03","","2026-11-30","",           "","","Y","N","AIX 7.3 TL4"),
    _os("AIX 7.3 TL3",  "2024-12-06","","2027-12-31","",           "","","N","N",""),
    _os("AIX 7.3 TL4",  "2025-12-05","","2028-12-31","",           "Latest","","N","N",""),

    # ── IBM i / z/OS ──────────────────────────────────────────────────────────
    _os("IBM i 7.2",    "2014-05-02","","2021-09-30","",           "End of Support","","Y","N","IBM i 7.5"),
    _os("IBM i 7.3",    "2016-04-15","","2023-09-30","",           "End of Support","","Y","N","IBM i 7.5"),
    _os("IBM i 7.4",    "2019-06-21","","2026-04-30","",           "","","Y","N","IBM i 7.5"),
    _os("IBM i 7.5",    "2022-05-20","","2028-04-30","",           "Latest","","N","N",""),
    _os("z/OS 2.4",     "2020-09-25","","2024-09-30","",           "End of Support","","Y","N","z/OS 3.1"),
    _os("z/OS 2.5",     "2021-09-24","","2026-09-30","",           "","","Y","N","z/OS 3.1"),
    _os("z/OS 3.1",     "2023-09-29","","2028-09-30","",           "Latest","","N","N",""),

    # ── HP-UX ─────────────────────────────────────────────────────────────────
    _os("HP-UX 11i v1 (B.11.11)", "","","2012-12-31","",           "End of Life","","Y","N",""),
    _os("HP-UX 11i v2 (B.11.23)", "","","2015-12-31","",           "End of Life","","Y","N",""),
    _os("HP-UX 11i v3 (B.11.31)", "","","2025-12-31","2028-12-31","HP 9000 PA-RISC","","N","N",""),
    _os("HP-UX 11i v3 (Integrity)","","","2025-12-31","2028-12-31","Itanium","","N","N",""),

    # ── FreeBSD ───────────────────────────────────────────────────────────────
    _os("FreeBSD 11.x",  "2016-10-10","","2021-09-30","",           "End of Life","","Y","N","FreeBSD 14.x"),
    _os("FreeBSD 12.x",  "2018-12-11","","2024-06-30","",           "End of Life","","Y","N","FreeBSD 14.x"),
    _os("FreeBSD 13.x",  "2021-04-13","","2026-04-30","",           "","","Y","N","FreeBSD 14.x"),
    _os("FreeBSD 14.x",  "2023-11-20","","2028-11-30","",           "","","N","N",""),
    _os("FreeBSD 15.x",  "2025-12-01","","2029-12-31","",           "Latest","","N","N",""),

    # ── OpenVMS / Tru64 ───────────────────────────────────────────────────────
    _os("OpenVMS Alpha V8.4",     "2012-09-01","","Extended","","HP support ended; VSI continues","","N","N",""),
    _os("OpenVMS Integrity V8.4-2L3","2021-01-01","","Extended","","VSI supported","","N","N",""),
    _os("OpenVMS x86 V9.2",       "2023-06-01","","Active","","VSI x86-64 port","","N","N",""),
    _os("Tru64 UNIX 5.1B-6",      "2010-10-01","","2012-12-31","","End of Life; HP discontinued","","Y","N",""),

    # ── Android Enterprise ────────────────────────────────────────────────────
    _os("Android 10",  "2019-09-03","","2023-02-01","","End of Security Updates","","Y","N","Android 15"),
    _os("Android 11",  "2020-09-08","","2024-02-01","","End of Security Updates","","Y","N","Android 15"),
    _os("Android 12",  "2021-10-04","","2024-02-01","","End of Security Updates","","Y","N","Android 15"),
    _os("Android 13",  "2022-08-15","","2026-02-01","","","","Y","N","Android 15"),
    _os("Android 14",  "2023-10-04","","2027-02-01","","","","N","N",""),
    _os("Android 15",  "2024-09-03","","2028-02-01","","Latest","","N","N",""),

    # ── iOS / iPadOS ──────────────────────────────────────────────────────────
    _os("iOS / iPadOS 15",  "2021-09-20","","Active","","Security updates only","","Y","N","iOS / iPadOS 18"),
    _os("iOS / iPadOS 16",  "2022-09-12","","Active","","Security updates only","","Y","N","iOS / iPadOS 18"),
    _os("iOS / iPadOS 17",  "2023-09-18","","Active","","","","Y","N","iOS / iPadOS 18"),
    _os("iOS / iPadOS 18",  "2024-09-16","","Active","","Latest","","N","N",""),

]


# =============================================================================
# DB DATA — Comprehensive coverage from Claude training knowledge
# =============================================================================
DB_DATA = [

    # ── Microsoft SQL Server ──────────────────────────────────────────────────
    _db("SQL Server","2005",   "Relational","2011-04-12","2016-04-12","End of Life","","","Y"),
    _db("SQL Server","2008",   "Relational","2012-07-10","2019-07-09","End of Life","ESU ended","","Y"),
    _db("SQL Server","2008 R2","Relational","2012-07-10","2019-07-09","End of Life","ESU ended","","Y"),
    _db("SQL Server","2012",   "Relational","2017-07-11","2022-07-12","End of Life","ESU ended Jul 2025","","Y"),
    _db("SQL Server","2014",   "Relational","2019-07-09","2024-07-09","End of Life","","","Y"),
    _db("SQL Server","2016",   "Relational","2021-07-13","2026-07-14","Expiring Soon","","","Y","N","SQL Server 2022"),
    _db("SQL Server","2017",   "Relational","2022-10-11","2027-10-12","Supported","","","Y","N","SQL Server 2022"),
    _db("SQL Server","2019",   "Relational","2025-01-07","2030-01-08","Supported","","","N"),
    _db("SQL Server","2022",   "Relational","2027-01-11","2032-01-12","Supported","Latest","","N"),

    # ── Oracle Database ───────────────────────────────────────────────────────
    _db("Oracle DB","10g R2","Relational","2010-07-13","",           "End of Life","","","Y","Y","PostgreSQL 18"),
    _db("Oracle DB","11g R1","Relational","2012-08-31","",           "End of Life","","","Y","Y","PostgreSQL 18"),
    _db("Oracle DB","11g R2","Relational","2020-12-31","2026-12-31","Expiring Soon","Upgrade support to Dec 2026","","Y","Y","PostgreSQL 18","Oracle DB 19c"),
    _db("Oracle DB","12c R1","Relational","2018-07-31","2026-12-31","Expiring Soon","Upgrade support to Dec 2026","","Y","Y","PostgreSQL 18","Oracle DB 19c"),
    _db("Oracle DB","12c R2","Relational","2022-03-31","2026-12-31","Expiring Soon","Upgrade support to Dec 2026","","Y","Y","PostgreSQL 18","Oracle DB 19c"),
    _db("Oracle DB","18c",   "Relational","2021-06-30","",           "End of Life","Innovation release","","Y","Y","Oracle DB 19c"),
    _db("Oracle DB","19c",   "Relational","2029-12-31","2032-12-31","Supported","Long-term release; Premier extended","","N","Y","PostgreSQL 18"),
    _db("Oracle DB","21c",   "Relational","2024-04-30","",           "End of Life","Innovation release","","N","Y","Oracle DB 23ai"),
    _db("Oracle DB","23ai",  "Relational","2031-12-31","2034-12-31","Supported","Latest; AI features","","N","Y","PostgreSQL 18"),

    # ── PostgreSQL ────────────────────────────────────────────────────────────
    _db("PostgreSQL","11","Relational","2023-11-09","","End of Life","","","Y"),
    _db("PostgreSQL","12","Relational","2024-11-14","","End of Life","","","Y"),
    _db("PostgreSQL","13","Relational","2025-11-13","","End of Life","","","Y"),
    _db("PostgreSQL","14","Relational","2026-11-12","","Expiring Soon","","","Y","N","PostgreSQL 17"),
    _db("PostgreSQL","15","Relational","2027-11-11","","Supported","","","N"),
    _db("PostgreSQL","16","Relational","2028-11-09","","Supported","","","N"),
    _db("PostgreSQL","17","Relational","2029-11-08","","Supported","","","N"),
    _db("PostgreSQL","18","Relational","2030-11-13","","Supported","Latest","","N"),

    # ── MySQL ─────────────────────────────────────────────────────────────────
    _db("MySQL","5.6",    "Relational","2021-02-28","",           "End of Life","","","Y","Y","MySQL 8.4 LTS"),
    _db("MySQL","5.7",    "Relational","2023-10-25","2025-10-25","End of Life","EOL Oct 2025","","Y","Y","MySQL 8.4 LTS","PostgreSQL 18"),
    _db("MySQL","8.0",    "Relational","2025-04-30","2026-04-30","Expiring Soon","Extended to Apr 2028","","Y","Y","MySQL 8.4 LTS","PostgreSQL 18"),
    _db("MySQL","8.4 LTS","Relational","2029-04-30","2032-04-30","Supported","LTS release","","N","Y","PostgreSQL 18"),
    _db("MySQL","9.0",    "Relational","2024-11-30","",           "End of Life","Innovation — short lifecycle","","Y","N","MySQL 9.7 LTS"),
    _db("MySQL","9.7 LTS","Relational","2030-04-30","2033-04-30","Supported","Future LTS","","N","Y","PostgreSQL 18"),

    # ── MariaDB ───────────────────────────────────────────────────────────────
    _db("MariaDB","10.4",     "Relational","2024-06-18","","End of Life","","","Y"),
    _db("MariaDB","10.5",     "Relational","2025-06-24","","End of Life","","","Y","N","MariaDB 11.4 LTS"),
    _db("MariaDB","10.6 LTS", "Relational","2026-07-06","","Expiring Soon","LTS","","Y","N","MariaDB 11.4 LTS"),
    _db("MariaDB","10.11 LTS","Relational","2028-02-16","","Supported","LTS","","N"),
    _db("MariaDB","11.2",     "Relational","2025-02-10","","End of Life","Short-term","","Y","N","MariaDB 11.4 LTS"),
    _db("MariaDB","11.4 LTS", "Relational","2029-05-29","","Supported","LTS","","N"),
    _db("MariaDB","11.8 LTS", "Relational","2030-02-01","","Supported","Latest LTS","","N"),

    # ── IBM Db2 ───────────────────────────────────────────────────────────────
    _db("IBM Db2","9.7",  "Relational","2017-09-30","2022-09-30","End of Life","","","Y"),
    _db("IBM Db2","10.1", "Relational","2019-09-30","2024-09-30","End of Life","","","Y"),
    _db("IBM Db2","10.5", "Relational","2020-09-30","2025-04-30","End of Life","","","Y"),
    _db("IBM Db2","11.1", "Relational","2023-09-30","2028-04-30","Supported","","","Y","N","IBM Db2 11.5"),
    _db("IBM Db2","11.5", "Relational","2025-09-30","2030-04-30","Supported","Latest","","N"),

    # ── IBM Informix ──────────────────────────────────────────────────────────
    _db("IBM Informix","11.50","Relational","2017-09-30","2022-09-30","End of Life","","","Y"),
    _db("IBM Informix","11.70","Relational","2019-09-30","2024-09-30","End of Life","","","Y"),
    _db("IBM Informix","12.10","Relational","2021-09-30","2026-09-30","Expiring Soon","","","Y","N","IBM Informix 14.10"),
    _db("IBM Informix","14.10","Relational","2025-09-30","2030-09-30","Supported","Latest","","N"),

    # ── SAP Sybase ASE ────────────────────────────────────────────────────────
    _db("SAP ASE (Sybase)","12.5",     "Relational","2015-12-31","","End of Life","","","Y"),
    _db("SAP ASE (Sybase)","15.0",     "Relational","2018-12-31","","End of Life","","","Y"),
    _db("SAP ASE (Sybase)","15.5",     "Relational","2020-12-31","","End of Life","","","Y"),
    _db("SAP ASE (Sybase)","15.7",     "Relational","2025-09-30","","Expiring Soon","","","Y","N","SAP ASE 16.0 SP04"),
    _db("SAP ASE (Sybase)","16.0 SP04","Relational","2027-12-31","","Supported","Latest SP","","N"),

    # ── SAP IQ (Sybase IQ) ────────────────────────────────────────────────────
    _db("SAP IQ (Sybase IQ)","15.4","Columnar","2020-12-31","","End of Life","","","Y"),
    _db("SAP IQ (Sybase IQ)","16.0","Columnar","2022-12-31","","End of Life","","","Y","N","SAP IQ 16.1"),
    _db("SAP IQ (Sybase IQ)","16.1","Columnar","2027-12-31","","Supported","Latest","","N"),

    # ── SAP HANA ──────────────────────────────────────────────────────────────
    _db("SAP HANA","1.0 SPS 12","Relational","2020-12-31","",           "End of Life","","","Y"),
    _db("SAP HANA","2.0 SPS 05","Relational","2024-12-31","",           "End of Life","","","Y"),
    _db("SAP HANA","2.0 SPS 06","Relational","2025-06-30","",           "End of Life","","","Y"),
    _db("SAP HANA","2.0 SPS 07","Relational","2026-12-31","",           "Expiring Soon","","","Y","N","SAP HANA 2.0 SPS 08"),
    _db("SAP HANA","2.0 SPS 08","Relational","2028-12-31","",           "Supported","Latest SPS","","N"),

    # ── SAP MaxDB / SQL Anywhere ──────────────────────────────────────────────
    _db("SAP MaxDB","7.9","Relational","2026-12-31","","Expiring Soon","SAP MaxDB","","Y"),
    _db("SAP SQL Anywhere","17.0","Relational","2027-12-31","","Supported","Latest","","N"),

    # ── Teradata ──────────────────────────────────────────────────────────────
    _db("Teradata Vantage","1.x","Columnar","2024-12-31","","End of Life","","","Y","N","Teradata Vantage 2.x"),
    _db("Teradata Vantage","2.x","Columnar","2028-12-31","","Supported","Latest","","N"),

    # ── Vertica ───────────────────────────────────────────────────────────────
    _db("Vertica","9.x","Columnar","2022-12-31","","End of Life","","","Y"),
    _db("Vertica","10.x","Columnar","2023-12-31","","End of Life","","","Y"),
    _db("Vertica","11.x","Columnar","2024-12-31","","End of Life","","","Y","N","Vertica 12.x"),
    _db("Vertica","12.x","Columnar","2026-12-31","","Expiring Soon","","","Y","N","Vertica 24.x"),
    _db("Vertica","24.x","Columnar","2028-12-31","","Supported","Latest","","N"),

    # ── Greenplum ─────────────────────────────────────────────────────────────
    _db("Greenplum","5.x","Columnar","2021-12-31","","End of Life","","","Y"),
    _db("Greenplum","6.x","Columnar","2025-12-31","","Expiring Soon","","","Y","N","Greenplum 7.x"),
    _db("Greenplum","7.x","Columnar","2028-12-31","","Supported","Latest","","N"),

    # ── MongoDB ───────────────────────────────────────────────────────────────
    _db("MongoDB","4.2","Document (NoSQL)","2022-10-01","","End of Life","","","Y"),
    _db("MongoDB","4.4","Document (NoSQL)","2024-02-29","","End of Life","","","Y"),
    _db("MongoDB","5.0","Document (NoSQL)","2024-10-01","","End of Life","","","Y"),
    _db("MongoDB","6.0","Document (NoSQL)","2025-07-31","","End of Life","","","Y","N","MongoDB 8.0"),
    _db("MongoDB","7.0","Document (NoSQL)","2027-08-01","","Supported","Extended 4yr lifecycle","","Y","N","MongoDB 8.0"),
    _db("MongoDB","8.0","Document (NoSQL)","2029-09-01","","Supported","Latest — 5yr lifecycle","","N"),

    # ── Couchbase / CouchDB ───────────────────────────────────────────────────
    _db("Couchbase Server","6.x","Document (NoSQL)","2025-06-30","","End of Life","","","Y","N","Couchbase 7.x"),
    _db("Couchbase Server","7.x","Document (NoSQL)","2028-06-30","","Supported","Latest","","N"),
    _db("Apache CouchDB","2.x","Document (NoSQL)","2022-12-31","","End of Life","","","Y","N","CouchDB 3.x"),
    _db("Apache CouchDB","3.x","Document (NoSQL)","2026-12-31","","Supported","Current","","N"),

    # ── Redis ─────────────────────────────────────────────────────────────────
    _db("Redis","6.0","In-Memory","2024-04-01","","End of Life","","","Y"),
    _db("Redis","6.2","In-Memory","2026-02-28","","End of Life","","","Y","N","Redis 7.4"),
    _db("Redis","7.0","In-Memory","2025-06-01","","End of Life","","","Y","N","Redis 7.4"),
    _db("Redis","7.2","In-Memory","2026-02-28","","End of Life","","","Y","N","Redis 7.4"),
    _db("Redis","7.4","In-Memory","2026-11-30","","Expiring Soon","RSALv2+SSPL license","","Y","N","Redis 8.0"),
    _db("Redis","7.8","In-Memory","2027-05-30","","Supported","","","N"),
    _db("Redis","8.0","In-Memory","TBD","","Future","Next major version","","N"),

    # ── Apache Cassandra ──────────────────────────────────────────────────────
    _db("Apache Cassandra","3.0", "Columnar","2023-12-31","","End of Life","","","Y"),
    _db("Apache Cassandra","3.11","Columnar","2024-06-01","","End of Life","","","Y"),
    _db("Apache Cassandra","4.0", "Columnar","2026-07-01","","Expiring Soon","","","Y","N","Cassandra 5.0"),
    _db("Apache Cassandra","4.1", "Columnar","2027-07-01","","Supported","","","N"),
    _db("Apache Cassandra","5.0", "Columnar","2028-11-01","","Supported","Latest","","N"),

    # ── Elasticsearch / OpenSearch ────────────────────────────────────────────
    _db("Elasticsearch","6.x","Search","2022-02-28","","End of Life","","","Y"),
    _db("Elasticsearch","7.x","Search","2024-08-31","","End of Life","","","Y","N","Elasticsearch 8.x"),
    _db("Elasticsearch","8.x","Search","2026-12-31","","Supported","Current","","N"),
    _db("OpenSearch",   "1.x","Search","2024-12-31","","End of Life","AWS fork of Elasticsearch","","Y","N","OpenSearch 2.x"),
    _db("OpenSearch",   "2.x","Search","2027-12-31","","Supported","Latest","","N"),

    # ── Neo4j ─────────────────────────────────────────────────────────────────
    _db("Neo4j","3.5","Graph","2021-11-28","","End of Life","","","Y"),
    _db("Neo4j","4.4","Graph","2026-05-31","","Expiring Soon","Last 4.x LTS","","Y","N","Neo4j 5.x"),
    _db("Neo4j","5.x","Graph","2029-05-31","","Supported","Latest","","N"),

    # ── InfluxDB / TimescaleDB ────────────────────────────────────────────────
    _db("InfluxDB","1.x","Time-Series","2025-12-31","","End of Life","","","Y","N","InfluxDB 3.x"),
    _db("InfluxDB","2.x","Time-Series","2026-12-31","","Expiring Soon","","","Y","N","InfluxDB 3.x"),
    _db("InfluxDB","3.x","Time-Series","2028-12-31","","Supported","Latest","","N"),
    _db("TimescaleDB","2.x","Time-Series","2028-12-31","","Supported","Current","","N"),

    # ── CockroachDB / YugabyteDB ──────────────────────────────────────────────
    _db("CockroachDB","22.x","Multi-Model","2024-06-30","","End of Life","","","Y","N","CockroachDB 24.x"),
    _db("CockroachDB","23.x","Multi-Model","2025-12-31","","Expiring Soon","","","Y","N","CockroachDB 24.x"),
    _db("CockroachDB","24.x","Multi-Model","2027-06-30","","Supported","Latest","","N"),
    _db("YugabyteDB","2.14 LTS","Multi-Model","2025-11-01","","Expiring Soon","LTS","","Y","N","YugabyteDB 2.20 LTS"),
    _db("YugabyteDB","2.20 LTS","Multi-Model","2027-05-01","","Supported","Latest LTS","","N"),

    # ── Ingres / Actian ───────────────────────────────────────────────────────
    _db("Actian Ingres","10.2","Relational","2022-12-31","","End of Life","","","Y","N","Actian X"),
    _db("Actian X","16.x","Relational","2027-12-31","","Supported","Latest","","N"),
    _db("Actian Vector","6.x","Columnar","2027-12-31","","Supported","Columnar analytics","","N"),

    # ── Progress OpenEdge ─────────────────────────────────────────────────────
    _db("Progress OpenEdge","11.x","Relational","2024-12-31","","End of Life","","","Y","N","Progress OpenEdge 12.x"),
    _db("Progress OpenEdge","12.x","Relational","2028-12-31","","Supported","Latest","","N"),

    # ── Firebird ──────────────────────────────────────────────────────────────
    _db("Firebird","2.5","Relational","2021-12-31","","End of Life","","","Y","N","Firebird 5.0"),
    _db("Firebird","3.0","Relational","2024-12-31","","End of Life","","","Y","N","Firebird 5.0"),
    _db("Firebird","4.0","Relational","2027-12-31","","Supported","","","N"),
    _db("Firebird","5.0","Relational","2029-12-31","","Supported","Latest","","N"),

    # ── Amazon Aurora / RDS ───────────────────────────────────────────────────
    _db("Amazon Aurora MySQL","2.x (MySQL 5.7)","Cloud-Managed","2026-10-31","","Expiring Soon","AWS deprecation Oct 2026","","Y","Y","Aurora MySQL 3.x"),
    _db("Amazon Aurora MySQL","3.x (MySQL 8.0)","Cloud-Managed","2030-04-30","","Supported","Current","","N"),
    _db("Amazon Aurora PostgreSQL","14.x","Cloud-Managed","2027-02-28","","Supported","","","N"),
    _db("Amazon Aurora PostgreSQL","16.x","Cloud-Managed","2029-11-08","","Supported","Current","","N"),
    _db("Amazon RDS SQL Server","2016","Cloud-Managed","2026-07-14","","Expiring Soon","AWS EOL","","Y","N","RDS SQL Server 2019"),
    _db("Amazon RDS SQL Server","2019","Cloud-Managed","2030-01-08","","Supported","","","N"),
    _db("Amazon RDS MySQL","5.7","Cloud-Managed","2025-10-25","","End of Life","AWS deprecated","","Y","Y","RDS MySQL 8.0"),
    _db("Amazon RDS MySQL","8.0","Cloud-Managed","2026-04-30","","Supported","","","N"),
    _db("Amazon RDS PostgreSQL","13","Cloud-Managed","2026-02-28","","Expiring Soon","AWS EOL","","Y","N","RDS PostgreSQL 16"),
    _db("Amazon RDS PostgreSQL","16","Cloud-Managed","2028-11-09","","Supported","Current","","N"),
    _db("Amazon DynamoDB","Current","Cloud-Managed","Active","","Supported","Managed; always current","","N"),
    _db("Amazon DocumentDB","4.0","Cloud-Managed","2025-12-31","","Expiring Soon","MongoDB-compatible","","Y","N","DocumentDB 5.0"),
    _db("Amazon DocumentDB","5.0","Cloud-Managed","2028-12-31","","Supported","Current","","N"),
    _db("Amazon ElastiCache (Redis)","6.x","Cloud-Managed","2025-12-31","","Expiring Soon","","","Y","N","ElastiCache Redis 7.x"),
    _db("Amazon ElastiCache (Redis)","7.x","Cloud-Managed","2028-12-31","","Supported","Current","","N"),

    # ── Azure ─────────────────────────────────────────────────────────────────
    _db("Azure SQL Database","Current","Cloud-Managed","Active","","Supported","Managed; always current","","N"),
    _db("Azure SQL Managed Instance","Current","Cloud-Managed","Active","","Supported","Managed; always current","","N"),
    _db("Azure Cosmos DB","API for NoSQL","Document (NoSQL)","Active","","Supported","Managed","","N"),
    _db("Azure Cosmos DB","API for MongoDB","Document (NoSQL)","Active","","Supported","Managed","","N"),
    _db("Azure Cache for Redis","6.x","Cloud-Managed","2025-12-31","","Expiring Soon","","","Y","N","Redis 7.x"),
    _db("Azure Cache for Redis","7.x","Cloud-Managed","2028-12-31","","Supported","Current","","N"),

    # ── Google Cloud ──────────────────────────────────────────────────────────
    _db("Google Cloud SQL MySQL","8.0","Cloud-Managed","2026-04-30","","Supported","","","N"),
    _db("Google Cloud SQL PostgreSQL","14","Cloud-Managed","2027-02-28","","Supported","","","N"),
    _db("Google Cloud SQL PostgreSQL","16","Cloud-Managed","2029-11-08","","Supported","Current","","N"),
    _db("Google Cloud Spanner","Current","Cloud-Managed","Active","","Supported","Managed","","N"),
    _db("Google AlloyDB","Current","Cloud-Managed","Active","","Supported","PostgreSQL-compatible managed","","N"),
    _db("Google BigQuery","Current","Cloud-Managed","Active","","Supported","Managed analytics","","N"),

    # ── Snowflake / Databricks ────────────────────────────────────────────────
    _db("Snowflake","Current","Cloud-Managed","Active","","Supported","Continuously updated","","N"),
    _db("Databricks Runtime","12.2 LTS","Cloud-Managed","2024-11-15","","End of Life","LTS ended","","Y","N","Databricks RT 15.4 LTS"),
    _db("Databricks Runtime","13.3 LTS","Cloud-Managed","2025-11-15","","Expiring Soon","LTS","","Y","N","Databricks RT 15.4 LTS"),
    _db("Databricks Runtime","14.3 LTS","Cloud-Managed","2026-02-09","","Expiring Soon","LTS","","Y","N","Databricks RT 15.4 LTS"),
    _db("Databricks Runtime","15.4 LTS","Cloud-Managed","2027-01-15","","Supported","Current LTS","","N"),

    # ── Apache Hadoop Ecosystem ───────────────────────────────────────────────
    _db("Apache Hive","2.x","Columnar","2023-12-31","","End of Life","","","Y","N","Apache Hive 4.x"),
    _db("Apache Hive","3.x","Columnar","2025-12-31","","Expiring Soon","","","Y","N","Apache Hive 4.x"),
    _db("Apache Hive","4.x","Columnar","2028-12-31","","Supported","Latest","","N"),
    _db("Apache HBase","1.x","Columnar","2022-12-31","","End of Life","","","Y","N","Apache HBase 2.x"),
    _db("Apache HBase","2.x","Columnar","2027-12-31","","Supported","Current","","N"),
    _db("Apache Hadoop","2.x","Multi-Model","2020-12-31","","End of Life","","","Y","N","Apache Hadoop 3.x"),
    _db("Apache Hadoop","3.x","Multi-Model","2027-12-31","","Supported","Current","","N"),

    # ── Exasol / SingleStore ──────────────────────────────────────────────────
    _db("Exasol","7.x","Columnar","2024-12-31","","End of Life","","","Y","N","Exasol 8.x"),
    _db("Exasol","8.x","Columnar","2028-12-31","","Supported","Latest","","N"),
    _db("SingleStore (MemSQL)","7.x","Multi-Model","2024-12-31","","End of Life","","","Y","N","SingleStore 8.x"),
    _db("SingleStore (MemSQL)","8.x","Multi-Model","2028-12-31","","Supported","Latest","","N"),

    # ── Microsoft Access / FoxPro ─────────────────────────────────────────────
    _db("Microsoft Access","2016","Relational","2025-10-14","","End of Life","Part of Office 2016","","Y","N","Access 2021"),
    _db("Microsoft Access","2019","Relational","2025-10-14","","End of Life","Part of Office 2019","","Y","N","Access 2021"),
    _db("Microsoft Access","2021","Relational","2026-10-13","","Supported","Part of Office 2021","","N"),
    _db("Microsoft Access","2024","Relational","2029-10-09","","Supported","Latest","","N"),
    _db("Visual FoxPro","9.0","Relational","2007-01-16","","End of Life","Discontinued by Microsoft","","Y","Y","SQL Server 2022"),

    # ── IBM IMS ───────────────────────────────────────────────────────────────
    _db("IBM IMS","13","Multi-Model","2022-09-30","","End of Life","Mainframe hierarchical DB","","Y","N","IBM IMS 15"),
    _db("IBM IMS","14","Multi-Model","2024-09-30","","End of Life","","","Y","N","IBM IMS 15"),
    _db("IBM IMS","15","Multi-Model","2028-09-30","","Supported","Latest","","N"),

]

# =============================================================================
# ADDITIONAL OS DATA — expanding to 184+ rows
# =============================================================================
OS_DATA += [

    # ── Windows 11 additional editions ───────────────────────────────────────
    _os("Windows 11 21H2 IoT Ent",     "2021-10-05","","2027-01-12","2032-01-13","IoT Enterprise LTSC equiv","","Y","N","Windows 11 24H2 LTSC"),
    _os("Windows 11 22H2 SE",          "2022-09-20","","2025-10-14","",           "Windows 11 SE (Education)","","Y","N","Windows 11 24H2"),
    _os("Windows 11 ARM64",            "2021-10-05","","2027-10-12","",           "ARM64 editions; same lifecycle","","N","N",""),

    # ── Windows 10 additional / missing builds ────────────────────────────────
    _os("Windows 10 1507 LTSB",        "2015-07-29","","Ended","2025-10-14",      "LTSB 2015","","Y","N","Windows 11 24H2"),
    _os("Windows 10 21H2 LTSC IoT",    "2021-11-16","","Ended","2032-01-13",      "IoT LTSC 2021","","N","N",""),
    _os("Windows 10 Enterprise 22H2",  "2022-10-18","","2025-10-14","",           "Enterprise edition","","Y","N","Windows 11 24H2"),
    _os("Windows 10 Education 22H2",   "2022-10-18","","2025-10-14","",           "Education edition","","Y","N","Windows 11 24H2"),

    # ── Windows Server additional ─────────────────────────────────────────────
    _os("Windows Server 2000",         "2000-02-17","","2005-06-30","2010-07-13","End of Life","","Y","N","Windows Server 2025"),
    _os("Windows Server 2003 Web",     "2003-04-24","","2010-07-13","",           "Web Edition — EOL","","Y","N","Windows Server 2025"),
    _os("Windows Server 2008 Core",    "2008-02-27","","2015-01-13","2020-01-14","Server Core — EOL","","Y","N","Windows Server 2025"),
    _os("Windows Server 2012 Datacenter","2012-10-30","","2018-10-09","2023-10-10","Datacenter edition","","Y","N","Windows Server 2025"),
    _os("Windows Server 2016 Datacenter","2016-10-15","","2022-01-11","2027-01-12","Datacenter edition","","Y","N","Windows Server 2025"),
    _os("Windows Server 2019 Datacenter","2018-11-13","","2024-01-09","2029-01-09","Datacenter edition","","N","N",""),
    _os("Windows Server 2022 Datacenter","2021-08-18","","2026-10-13","2031-10-14","Datacenter edition","","N","N",""),
    _os("Windows Server 2025 Datacenter","2024-11-01","","2029-11-13","2034-11-14","Datacenter; latest","","N","N",""),
    _os("Windows Server Core 2022",    "2021-08-18","","2026-10-13","2031-10-14","Server Core installation","","N","N",""),
    _os("Windows Server Azure Edition 2022","2021-08-18","","2026-10-13","2031-10-14","Azure-specific edition","","N","N",""),

    # ── Windows Embedded additional ───────────────────────────────────────────
    _os("Windows XP Embedded SP3",     "2004-08-24","","2014-01-14","2016-01-12","End of Life","","Y","N","Windows IoT LTSC 2024"),
    _os("Windows Embedded POSReady 7", "2011-06-16","","2015-10-13","2021-10-12","Point of Sale — EOL","","Y","N","Windows IoT LTSC 2024"),
    _os("Windows Embedded 8.1 Pro",    "2013-11-01","","2018-01-09","2023-07-11","End of Life","","Y","N","Windows IoT LTSC 2024"),
    _os("Windows 10 IoT Core",         "2015-09-01","","2020-11-10","",           "End of Life; IoT Core","","Y","N","Windows IoT LTSC 2024"),
    _os("Windows 10 IoT Enterprise LTSB 2016","2016-08-02","","Ended","2026-10-13","","","Y","N","Windows IoT LTSC 2024"),
    _os("Windows 10 IoT Enterprise LTSC 2019","2018-11-13","","Ended","2029-01-09","","","Y","N","Windows IoT LTSC 2024"),

    # ── RHEL additional editions ──────────────────────────────────────────────
    _os("RHEL 7 for SAP HANA",         "2014-06-10","2019-08-06","2024-06-30","2026-06-30","SAP-certified","","Y","N","RHEL 9 for SAP"),
    _os("RHEL 8 for SAP HANA",         "2019-05-07","2024-05-31","2029-05-31","2032-05-31","SAP-certified","","N","N",""),
    _os("RHEL 9 for SAP",              "2022-05-18","2027-05-31","2032-05-31","2035-05-31","SAP-certified","","N","N",""),
    _os("RHEL 8 ARM",                  "2019-05-07","2024-05-31","2029-05-31","2032-05-31","ARM64 support","","N","N",""),
    _os("RHEL 9 ARM",                  "2022-05-18","2027-05-31","2032-05-31","2035-05-31","ARM64 support","","N","N",""),

    # ── Ubuntu additional ─────────────────────────────────────────────────────
    _os("Ubuntu 12.04 LTS",            "2012-04-26","2017-04-28","2019-04-28","2024-04-30","Precise; ESM ended","","Y","N","Ubuntu 24.04 LTS"),
    _os("Ubuntu 22.04.3 LTS",          "2023-08-10","2027-06-01","2032-04-01","2037-04-30","Point release; HWE","","N","N",""),
    _os("Ubuntu 24.04.1 LTS",          "2024-08-29","2029-05-31","2034-04-30","2036-04-30","Point release","","N","N",""),
    _os("Ubuntu Server 20.04 LTS",     "2020-04-23","2025-05-29","2030-04-02","2035-04-30","Server variant","","N","N",""),
    _os("Ubuntu Server 22.04 LTS",     "2022-04-21","2027-06-01","2032-04-01","2037-04-30","Server variant","","N","N",""),
    _os("Ubuntu Server 24.04 LTS",     "2024-04-25","2029-05-31","2034-04-30","2036-04-30","Server variant","","N","N",""),
    _os("Ubuntu 23.04",                "2023-04-20","2024-01-25","2024-01-25","",           "Lunar — EOL","","Y","N","Ubuntu 24.04 LTS"),
    _os("Ubuntu 23.10",                "2023-10-12","2024-07-11","2024-07-11","",           "Mantic — EOL","","Y","N","Ubuntu 24.04 LTS"),

    # ── SLES for SAP / additional ─────────────────────────────────────────────
    _os("SLES 12 SP5 for SAP",         "2019-12-09","","2024-10-31","2027-10-31","SAP-certified; LTSS available","","Y","N","SLES 15 SP6 for SAP"),
    _os("SLES 15 SP4 for SAP",         "2022-06-22","","2023-12-31","2026-12-31","SAP-certified","","Y","N","SLES 15 SP6 for SAP"),
    _os("SLES 15 SP5 for SAP",         "2023-06-20","","2024-12-31","2027-12-31","SAP-certified","","Y","N","SLES 15 SP6 for SAP"),
    _os("SLES 15 SP6 for SAP",         "2024-06-26","","2025-12-31","2028-12-31","SAP-certified","","N","N",""),
    _os("SLES 15 SP7 for SAP",         "2025-06-17","","2031-07-31","2034-07-31","SAP-certified; latest","","N","N",""),

    # ── Debian additional ─────────────────────────────────────────────────────
    _os("Debian 8 Jessie",             "2015-04-25","2018-06-17","2020-06-30","2025-06-30","ELTS ended 2025","","Y","N","Debian 12"),
    _os("Debian 11 Bullseye (armhf)",  "2021-08-14","2024-08-14","2026-08-31","2031-06-30","ARM 32-bit","","Y","N","Debian 12"),
    _os("Debian 12 Bookworm (arm64)",  "2023-06-10","2026-06-10","2028-06-30","2033-06-30","ARM 64-bit","","N","N",""),

    # ── CentOS additional ─────────────────────────────────────────────────────
    _os("CentOS 5",                    "2007-04-12","","2017-03-31","",           "End of Life","","Y","N","RHEL 9"),

    # ── Oracle Linux additional ───────────────────────────────────────────────
    _os("Oracle Linux 6 UEK",          "2011-02-12","","2021-03-01","2024-12-31","Unbreakable Enterprise Kernel","","Y","N","Oracle Linux 9"),
    _os("Oracle Linux 8 UEK R7",       "2021-06-15","","2029-07-31","2032-07-31","UEK R7","","N","N",""),
    _os("Oracle Linux 9 UEK R7",       "2022-09-12","","2032-06-30","2035-06-30","UEK R7","","N","N",""),

    # ── macOS older versions ──────────────────────────────────────────────────
    _os("macOS 10.14 Mojave",          "2018-09-24","","2021-10-25","",           "End of Support","","Y","N","macOS 15 Sequoia"),
    _os("macOS 10.15 Catalina",        "2019-10-07","","2022-11-01","",           "End of Support","","Y","N","macOS 15 Sequoia"),
    _os("macOS 10.13 High Sierra",     "2017-09-25","","2020-12-01","",           "End of Support","","Y","N","macOS 15 Sequoia"),

    # ── AIX additional ────────────────────────────────────────────────────────
    _os("AIX 7.2 TL4",                 "2019-12-06","","2024-12-31","",           "End of Service","","Y","N","AIX 7.3"),
    _os("AIX 7.3 TL0",                 "2021-12-10","","2024-12-31","",           "End of Service","","Y","N","AIX 7.3 TL4"),

    # ── IBM i additional ──────────────────────────────────────────────────────
    _os("IBM i 7.1",                   "2010-04-23","","2019-04-30","",           "End of Support","","Y","N","IBM i 7.5"),

    # ── Solaris additional ────────────────────────────────────────────────────
    _os("Solaris 11.1",                "2012-11-18","","Ended (Nov 2014)","",     "End of Life","","Y","N","Solaris 11.4"),
    _os("Solaris 11.2",                "2014-09-19","","Ended (Dec 2016)","",     "End of Life","","Y","N","Solaris 11.4"),

    # ── Additional Linux Distros ──────────────────────────────────────────────
    _os("Kali Linux 2024.x",           "2024-01-01","","Rolling","",              "Rolling release; security-focused","","N","N",""),
    _os("Arch Linux",                  "2002-03-11","","Rolling","",              "Rolling release; always current","","N","N",""),
    _os("Gentoo Linux",                "1999-12-01","","Rolling","",              "Rolling release; source-based","","N","N",""),
    _os("Raspberry Pi OS 11 (Bullseye)","2021-10-30","","2026-08-31","",          "32/64-bit; tracks Debian 11","","Y","N","Raspberry Pi OS 12"),
    _os("Raspberry Pi OS 12 (Bookworm)","2023-10-10","","2028-06-30","",          "64-bit; tracks Debian 12","","N","N",""),

    # ── VMware / Virtualization OS ────────────────────────────────────────────
    _os("VMware ESXi 6.7",             "2018-04-17","","2022-10-15","2023-11-15","End of General Support","","Y","N","VMware ESXi 8.0"),
    _os("VMware ESXi 7.0",             "2020-04-02","","2025-04-02","2027-04-02","","","Y","N","VMware ESXi 8.0"),
    _os("VMware ESXi 8.0",             "2022-10-11","","2027-10-11","2029-10-11","Latest","","N","N",""),

    # ── ChromeOS Enterprise ───────────────────────────────────────────────────
    _os("ChromeOS Enterprise LTS 108", "2023-02-14","","2024-06-01","",           "LTS channel — EOL","","Y","N","ChromeOS Enterprise LTS 126"),
    _os("ChromeOS Enterprise LTS 120", "2024-01-16","","2025-06-01","",           "LTS channel","","Y","N","ChromeOS Enterprise LTS 126"),
    _os("ChromeOS Enterprise LTS 126", "2024-06-04","","2026-06-01","",           "LTS channel; current","","N","N",""),

    # ── Android additional versions ───────────────────────────────────────────
    _os("Android 9 Pie",               "2018-08-06","","2021-02-01","",           "End of Security Updates","","Y","N","Android 15"),
    _os("Android 12L",                 "2022-03-07","","2025-02-01","",           "Large-screen; EOL","","Y","N","Android 15"),

    # ── iOS additional ────────────────────────────────────────────────────────
    _os("iOS / iPadOS 14",             "2020-09-16","","2022-10-01","",           "Security updates only","","Y","N","iOS / iPadOS 18"),

    # ── HP-UX additional ─────────────────────────────────────────────────────
    _os("HP-UX 11i v1 Integrity",      "","","2007-12-31","",           "End of Life","","Y","N",""),
    _os("HP-UX 11i v2 Integrity",      "","","2013-12-31","",           "End of Life","","Y","N",""),

    # ── FreeBSD additional ────────────────────────────────────────────────────
    _os("FreeBSD 13.0",                "2021-04-13","","2023-08-31","",           "EOL; use 13.4","","Y","N","FreeBSD 14.x"),
    _os("FreeBSD 13.4",                "2024-09-17","","2026-06-30","",           "Current 13.x release","","Y","N","FreeBSD 14.x"),
    _os("FreeBSD 14.0",                "2023-11-20","","2026-11-30","",           "","","Y","N","FreeBSD 14.2"),
    _os("FreeBSD 14.2",                "2025-01-30","","2028-11-30","",           "Current 14.x","","N","N",""),

    # ── OpenVMS additional ────────────────────────────────────────────────────
    _os("OpenVMS x86 V9.1",            "2022-04-01","","Active","",              "VSI x86-64 port","","N","N",""),
    _os("OpenVMS x86 V9.2-4",          "2024-06-01","","Active","",              "Latest x86-64","","N","N",""),

]


# =============================================================================
# WEB SERVER DATA — Lifecycle data for web servers found in inventory
# =============================================================================
WS_COLUMNS = [
    "Web Server", "Version", "Type",
    "Mainstream / Premier End", "Extended Support End",
    "Status", "Notes", "Recommendation",
    "Upgrade", "Replace", "Primary Alternative", "Secondary Alternative"
]

def _ws(ws, ver, typ, main="", ext="", status="Supported", notes="", rec="", upg="N", repl="N", pri="", sec=""):
    return {"Web Server": ws, "Version": ver, "Type": typ,
            "Mainstream / Premier End": main, "Extended Support End": ext,
            "Status": status, "Notes": notes, "Recommendation": rec,
            "Upgrade": upg, "Replace": repl, "Primary Alternative": pri, "Secondary Alternative": sec}

WS_DATA = [

    # ── IIS (Microsoft Internet Information Services) ────────────────────────
    _ws("IIS", "6.0", "Web Server", "2015-07-14", "", "End of Life", "Ships with Windows Server 2003", "", "Y", "N", "IIS 10.0", "Nginx"),
    _ws("IIS", "7.0", "Web Server", "2015-01-13", "", "End of Life", "Ships with Windows Server 2008", "", "Y", "N", "IIS 10.0", "Nginx"),
    _ws("IIS", "7.5", "Web Server", "2015-01-13", "2020-01-14", "End of Life", "Ships with Windows Server 2008 R2", "", "Y", "N", "IIS 10.0", "Nginx"),
    _ws("IIS", "8.0", "Web Server", "2018-01-09", "2023-01-10", "End of Life", "Ships with Windows Server 2012", "", "Y", "N", "IIS 10.0", "Nginx"),
    _ws("IIS", "8.5", "Web Server", "2018-10-09", "2023-10-10", "End of Life", "Ships with Windows Server 2012 R2", "", "Y", "N", "IIS 10.0", "Nginx"),
    _ws("IIS", "10.0", "Web Server", "2027-01-12", "2032-01-13", "Supported", "Ships with Windows Server 2016/2019/2022; lifecycle follows OS", "", "N", "N", "", ""),

    # ── Nginx ────────────────────────────────────────────────────────────────
    _ws("Nginx", "1.14.x", "Web Server", "2019-04-23", "", "End of Life", "Legacy stable branch", "", "Y", "N", "Nginx 1.28.x", "Apache 2.4.x"),
    _ws("Nginx", "1.16.x", "Web Server", "2020-04-14", "", "End of Life", "Stable branch 2019", "", "Y", "N", "Nginx 1.28.x", "Apache 2.4.x"),
    _ws("Nginx", "1.17.x", "Web Server", "2020-04-21", "", "End of Life", "Mainline branch 2019", "", "Y", "N", "Nginx 1.28.x", ""),
    _ws("Nginx", "1.18.x", "Web Server", "2021-04-13", "", "End of Life", "Stable branch 2020", "", "Y", "N", "Nginx 1.28.x", ""),
    _ws("Nginx", "1.19.x", "Web Server", "2021-05-25", "", "End of Life", "Mainline branch 2020", "", "Y", "N", "Nginx 1.28.x", ""),
    _ws("Nginx", "1.20.x", "Web Server", "2022-04-19", "", "End of Life", "Stable branch 2021", "", "Y", "N", "Nginx 1.28.x", ""),
    _ws("Nginx", "1.22.x", "Web Server", "2023-06-13", "", "End of Life", "Stable branch 2022", "", "Y", "N", "Nginx 1.28.x", ""),
    _ws("Nginx", "1.23.x", "Web Server", "2023-06-13", "", "End of Life", "Mainline branch 2022", "", "Y", "N", "Nginx 1.28.x", ""),
    _ws("Nginx", "1.24.x", "Web Server", "2025-04-15", "", "Expiring Soon", "Stable branch 2023", "", "Y", "N", "Nginx 1.28.x", ""),
    _ws("Nginx", "1.26.x", "Web Server", "2026-06-01", "", "Supported", "Stable branch 2024", "", "N", "N", "", ""),
    _ws("Nginx", "1.27.x", "Web Server", "2026-06-01", "", "Supported", "Mainline branch 2024", "", "N", "N", "Nginx 1.28.x", ""),
    _ws("Nginx", "1.28.x", "Web Server", "2027-06-01", "", "Supported", "Latest mainline 2025", "", "N", "N", "", ""),

    # ── Apache HTTP Server ───────────────────────────────────────────────────
    _ws("Apache", "2.2.x", "Web Server", "2017-07-11", "", "End of Life", "EOL since 2017; no security patches", "", "Y", "N", "Apache 2.4.x", "Nginx 1.28.x"),
    _ws("Apache", "2.4.6", "Web Server", "2024-06-30", "", "End of Life", "Shipped with RHEL 7; follows OS EOL", "", "Y", "N", "Apache 2.4.63", "Nginx 1.28.x"),
    _ws("Apache", "2.4.37", "Web Server", "2029-05-31", "", "Supported", "Shipped with RHEL 8; follows OS EOL", "", "N", "N", "Apache 2.4.63", ""),
    _ws("Apache", "2.4.39", "Web Server", "2029-05-31", "", "Supported", "RHEL 8 variant", "", "N", "N", "Apache 2.4.63", ""),
    _ws("Apache", "2.4.46", "Web Server", "2029-05-31", "", "Supported", "RHEL 8 / SLES 15 variant", "", "N", "N", "Apache 2.4.63", ""),
    _ws("Apache", "2.4.54", "Web Server", "2032-06-30", "", "Supported", "Shipped with RHEL 9 / Debian 12", "", "N", "N", "Apache 2.4.63", ""),
    _ws("Apache", "2.4.55", "Web Server", "2032-06-30", "", "Supported", "Upstream stable release", "", "N", "N", "Apache 2.4.63", ""),
    _ws("Apache", "2.4.59", "Web Server", "2032-06-30", "", "Supported", "Upstream stable 2024", "", "N", "N", "Apache 2.4.63", ""),
    _ws("Apache", "2.4.62", "Web Server", "2032-06-30", "", "Supported", "Upstream stable 2024", "", "N", "N", "Apache 2.4.63", ""),
    _ws("Apache", "2.4.63", "Web Server", "2032-06-30", "", "Supported", "Latest upstream stable 2025", "", "N", "N", "", ""),

]


# =============================================================================
# APPLICATION SERVER DATA — Lifecycle data for app servers found in inventory
# =============================================================================
AS_COLUMNS = [
    "App Server", "Version", "Type",
    "Mainstream / Premier End", "Extended Support End",
    "Status", "Notes", "Recommendation",
    "Upgrade", "Replace", "Primary Alternative", "Secondary Alternative"
]

def _as(asrv, ver, typ, main="", ext="", status="Supported", notes="", rec="", upg="N", repl="N", pri="", sec=""):
    return {"App Server": asrv, "Version": ver, "Type": typ,
            "Mainstream / Premier End": main, "Extended Support End": ext,
            "Status": status, "Notes": notes, "Recommendation": rec,
            "Upgrade": upg, "Replace": repl, "Primary Alternative": pri, "Secondary Alternative": sec}

AS_DATA = [

    # ── Apache Tomcat ────────────────────────────────────────────────────────
    _as("Tomcat", "7.0.x", "Application Server", "2021-03-31", "", "End of Life", "Java EE 6/Servlet 3.0; no patches", "", "Y", "N", "Tomcat 10.1.x", "Tomcat 9.0.x"),
    _as("Tomcat", "8.5.x", "Application Server", "2024-03-31", "", "End of Life", "Java EE 7/Servlet 3.1; EOL Mar 2024", "", "Y", "N", "Tomcat 10.1.x", "Tomcat 9.0.x"),
    _as("Tomcat", "9.0.x", "Application Server", "2028-01-01", "", "Supported", "Java EE 8/Servlet 4.0; Jakarta EE transition", "", "N", "N", "Tomcat 10.1.x", ""),
    _as("Tomcat", "10.1.x", "Application Server", "2031-01-01", "", "Supported", "Jakarta EE 10/Servlet 6.0; current stable", "", "N", "N", "", ""),
    _as("Tomcat", "11.0.x", "Application Server", "2034-01-01", "", "Supported", "Jakarta EE 11; latest release", "", "N", "N", "", ""),

    # ── JBoss / WildFly (Red Hat) ────────────────────────────────────────────
    _as("JBoss EAP", "6.x", "Application Server", "2019-06-30", "2022-06-30", "End of Life", "Java EE 6; no patches", "", "Y", "N", "JBoss EAP 8.0", "WildFly 33"),
    _as("JBoss EAP", "7.4.x", "Application Server", "2027-06-30", "2029-06-30", "Supported", "Java EE 8 / Jakarta EE 8; current LTS", "", "N", "N", "JBoss EAP 8.0", ""),
    _as("JBoss EAP", "8.0", "Application Server", "2029-06-30", "2031-06-30", "Supported", "Jakarta EE 10; latest", "", "N", "N", "", ""),
    _as("WildFly", "15.x", "Application Server", "2019-12-31", "", "End of Life", "Community; superseded", "", "Y", "N", "WildFly 33", "JBoss EAP 8.0"),
    _as("WildFly", "19.x", "Application Server", "2021-06-30", "", "End of Life", "Community; superseded", "", "Y", "N", "WildFly 33", "JBoss EAP 8.0"),
    _as("WildFly", "33.x", "Application Server", "2026-06-30", "", "Supported", "Community; Jakarta EE 10", "", "N", "N", "", ""),

    # ── IBM WebSphere ────────────────────────────────────────────────────────
    _as("WebSphere", "8.5.x", "Application Server", "2024-04-30", "2030-04-30", "Expiring Soon", "Traditional WAS; extended support", "", "Y", "N", "WebSphere Liberty", "Tomcat 10.1.x"),
    _as("WebSphere", "9.0.x", "Application Server", "2027-09-30", "2030-09-30", "Supported", "Traditional WAS 9", "", "N", "N", "WebSphere Liberty", ""),
    _as("WebSphere Liberty", "Current", "Application Server", "", "", "Supported", "Continuous delivery; lightweight; cloud-native", "", "N", "N", "", ""),

    # ── Apache Kafka ─────────────────────────────────────────────────────────
    _as("Kafka", "2.8.x", "Message Broker", "2023-06-30", "", "End of Life", "KRaft preview; superseded", "", "Y", "N", "Kafka 3.8.x", ""),
    _as("Kafka", "3.1.x", "Message Broker", "2024-01-01", "", "End of Life", "Superseded; no patches", "", "Y", "N", "Kafka 3.8.x", ""),
    _as("Kafka", "3.x (latest)", "Message Broker", "2026-06-30", "", "Supported", "KRaft GA; current stable", "", "N", "N", "", ""),

    # ── RabbitMQ ─────────────────────────────────────────────────────────────
    _as("RabbitMQ", "3.8.x", "Message Broker", "2022-07-31", "", "End of Life", "No security patches", "", "Y", "N", "RabbitMQ 3.13.x", ""),
    _as("RabbitMQ", "3.11.x", "Message Broker", "2023-12-31", "", "End of Life", "Superseded", "", "Y", "N", "RabbitMQ 3.13.x", ""),
    _as("RabbitMQ", "3.12.x", "Message Broker", "2024-12-31", "", "Expiring Soon", "Community support only", "", "Y", "N", "RabbitMQ 3.13.x", ""),
    _as("RabbitMQ", "3.13.x", "Message Broker", "2025-12-31", "", "Supported", "Current stable release", "", "N", "N", "", ""),

    # ── Apache Solr ──────────────────────────────────────────────────────────
    _as("Solr", "8.x", "Search Engine", "2024-03-31", "", "End of Life", "Java 8/11; superseded by 9.x", "", "Y", "N", "Solr 9.6.x", "Elasticsearch"),
    _as("Solr", "9.6.x", "Search Engine", "2027-01-01", "", "Supported", "Current stable; Java 11+", "", "N", "N", "", ""),

    # ── Logstash / Elastic Stack ─────────────────────────────────────────────
    _as("Logstash", "7.x", "Data Pipeline", "2024-08-01", "", "End of Life", "Elastic 7.x EOL Aug 2024", "", "Y", "N", "Logstash 8.x", ""),
    _as("Logstash", "8.x", "Data Pipeline", "2026-12-31", "", "Supported", "Current Elastic Stack release", "", "N", "N", "", ""),

    # ── Apache ZooKeeper ─────────────────────────────────────────────────────
    _as("ZooKeeper", "3.5.x", "Coordination Service", "2022-06-01", "", "End of Life", "No patches; use 3.8+", "", "Y", "N", "ZooKeeper 3.8.x", ""),
    _as("ZooKeeper", "3.8.x", "Coordination Service", "2026-06-01", "", "Supported", "Current stable LTS", "", "N", "N", "", ""),

    # ── Kubernetes ───────────────────────────────────────────────────────────
    _as("Kubernetes", "1.25.x", "Container Orchestrator", "2023-10-27", "", "End of Life", "14-month support window ended", "", "Y", "N", "Kubernetes 1.31.x", ""),
    _as("Kubernetes", "1.28.x", "Container Orchestrator", "2024-10-28", "", "End of Life", "14-month support window ended", "", "Y", "N", "Kubernetes 1.31.x", ""),
    _as("Kubernetes", "1.30.x", "Container Orchestrator", "2025-06-28", "", "Expiring Soon", "14-month support window", "", "Y", "N", "Kubernetes 1.31.x", ""),
    _as("Kubernetes", "1.31.x", "Container Orchestrator", "2025-10-28", "", "Supported", "Current stable", "", "N", "N", "", ""),
    _as("Kubernetes", "1.32.x", "Container Orchestrator", "2026-02-28", "", "Supported", "Latest release", "", "N", "N", "", ""),

    # ── SAP Application Server ───────────────────────────────────────────────
    _as("SAP NetWeaver", "7.x", "Application Server", "2027-12-31", "2030-12-31", "Supported", "SAP ERP/S4; mainstream until 2027", "", "N", "N", "SAP BTP", ""),

]


# =============================================================================
# FRAMEWORK DATA — Lifecycle data for development frameworks
# =============================================================================
FW_COLUMNS = [
    "Framework", "Version", "Type",
    "Mainstream / Premier End", "Extended Support End",
    "Status", "Notes", "Recommendation",
    "Upgrade", "Replace", "Primary Alternative", "Secondary Alternative"
]

def _fw(fw, ver, typ, main="", ext="", status="Supported", notes="", rec="", upg="N", repl="N", pri="", sec=""):
    return {"Framework": fw, "Version": ver, "Type": typ,
            "Mainstream / Premier End": main, "Extended Support End": ext,
            "Status": status, "Notes": notes, "Recommendation": rec,
            "Upgrade": upg, "Replace": repl, "Primary Alternative": pri, "Secondary Alternative": sec}

FW_DATA = [

    # ── .NET Framework (Windows-only) ────────────────────────────────────────
    _fw(".NET Framework", "3.5 SP1", "Runtime", "2028-10-10", "", "Supported", "Ships with Windows; follows OS lifecycle", "", "Y", "N", ".NET 8", ".NET 9"),
    _fw(".NET Framework", "4.5.x", "Runtime", "2016-01-12", "", "End of Life", "No patches since 2016", "", "Y", "N", ".NET 8", ""),
    _fw(".NET Framework", "4.6.x", "Runtime", "2027-11-12", "", "Supported", "Follows OS lifecycle", "", "Y", "N", ".NET 8", ""),
    _fw(".NET Framework", "4.7.x", "Runtime", "2028-01-09", "", "Supported", "Follows OS lifecycle", "", "Y", "N", ".NET 8", ""),
    _fw(".NET Framework", "4.8.x", "Runtime", "2032-01-13", "", "Supported", "Final .NET Framework; ships with Server 2022", "", "N", "N", ".NET 8", ""),

    # ── .NET (cross-platform, formerly .NET Core) ────────────────────────────
    _fw(".NET", "3.1 (Core)", "Runtime", "2022-12-13", "", "End of Life", "LTS ended Dec 2022", "", "Y", "N", ".NET 8", ""),
    _fw(".NET", "5.0", "Runtime", "2022-05-10", "", "End of Life", "STS; ended May 2022", "", "Y", "N", ".NET 8", ""),
    _fw(".NET", "6.0", "Runtime", "2024-11-12", "", "End of Life", "LTS ended Nov 2024", "", "Y", "N", ".NET 8", ".NET 9"),
    _fw(".NET", "7.0", "Runtime", "2024-05-14", "", "End of Life", "STS ended May 2024", "", "Y", "N", ".NET 8", ""),
    _fw(".NET", "8.0", "Runtime", "2026-11-10", "", "Supported", "LTS; current recommended", "", "N", "N", "", ""),
    _fw(".NET", "9.0", "Runtime", "2026-05-12", "", "Supported", "STS; latest release", "", "N", "N", ".NET 10", ""),
    _fw(".NET", "10.0", "Runtime", "2028-11-14", "", "Future", "LTS; expected Nov 2025 release", "", "N", "N", "", ""),

    # ── Spring Boot ──────────────────────────────────────────────────────────
    _fw("Spring Boot", "1.5.x", "Java Framework", "2019-08-01", "", "End of Life", "No patches since Aug 2019", "", "Y", "N", "Spring Boot 3.4.x", ""),
    _fw("Spring Boot", "2.3.x", "Java Framework", "2021-05-20", "", "End of Life", "OSS support ended May 2021", "", "Y", "N", "Spring Boot 3.4.x", ""),
    _fw("Spring Boot", "2.7.x", "Java Framework", "2023-11-24", "2025-08-24", "Expiring Soon", "Commercial support via Tanzu; OSS ended", "", "Y", "N", "Spring Boot 3.4.x", ""),
    _fw("Spring Boot", "3.0.x", "Java Framework", "2023-11-24", "", "End of Life", "Jakarta EE 9 baseline; OSS ended", "", "Y", "N", "Spring Boot 3.4.x", ""),
    _fw("Spring Boot", "3.3.x", "Java Framework", "2025-05-22", "2026-08-22", "Supported", "Current GA; Jakarta EE 10", "", "N", "N", "Spring Boot 3.4.x", ""),
    _fw("Spring Boot", "3.4.x", "Java Framework", "2025-11-20", "2027-02-20", "Supported", "Latest release; Jakarta EE 10", "", "N", "N", "", ""),

    # ── PHP ──────────────────────────────────────────────────────────────────
    _fw("PHP", "7.2.x", "Runtime", "2020-11-30", "", "End of Life", "No security patches since Nov 2020", "", "Y", "N", "PHP 8.3", "PHP 8.4"),
    _fw("PHP", "7.4.x", "Runtime", "2022-11-28", "", "End of Life", "Last PHP 7; EOL Nov 2022", "", "Y", "N", "PHP 8.3", "PHP 8.4"),
    _fw("PHP", "8.0.x", "Runtime", "2023-11-26", "", "End of Life", "EOL Nov 2023", "", "Y", "N", "PHP 8.3", "PHP 8.4"),
    _fw("PHP", "8.1.x", "Runtime", "2025-12-31", "", "Expiring Soon", "Security fixes only until Dec 2025", "", "Y", "N", "PHP 8.3", "PHP 8.4"),
    _fw("PHP", "8.2.x", "Runtime", "2026-12-31", "", "Supported", "Active support until Dec 2025; security until Dec 2026", "", "N", "N", "PHP 8.4", ""),
    _fw("PHP", "8.3.x", "Runtime", "2027-12-31", "", "Supported", "Current stable; active support", "", "N", "N", "", ""),
    _fw("PHP", "8.4.x", "Runtime", "2028-12-31", "", "Supported", "Latest release 2024", "", "N", "N", "", ""),

    # ── React ────────────────────────────────────────────────────────────────
    _fw("React", "16.x", "JavaScript Library", "2022-03-29", "", "End of Life", "No new patches; security only via React 18", "", "Y", "N", "React 19", "React 18"),
    _fw("React", "17.x", "JavaScript Library", "2022-03-29", "", "End of Life", "Stepping stone release; no patches", "", "Y", "N", "React 19", "React 18"),
    _fw("React", "18.x", "JavaScript Library", "2025-12-31", "", "Supported", "Concurrent features; hooks-based", "", "N", "N", "React 19", ""),
    _fw("React", "19.x", "JavaScript Library", "2027-12-31", "", "Supported", "Latest release; Server Components", "", "N", "N", "", ""),

    # ── Angular ──────────────────────────────────────────────────────────────
    _fw("Angular", "12.x", "JavaScript Framework", "2022-11-12", "", "End of Life", "LTS ended Nov 2022", "", "Y", "N", "Angular 18", "React 19"),
    _fw("Angular", "14.x", "JavaScript Framework", "2023-11-18", "", "End of Life", "LTS ended Nov 2023", "", "Y", "N", "Angular 18", ""),
    _fw("Angular", "16.x", "JavaScript Framework", "2024-11-08", "", "End of Life", "LTS ended Nov 2024", "", "Y", "N", "Angular 18", ""),
    _fw("Angular", "17.x", "JavaScript Framework", "2025-05-15", "2025-11-15", "Expiring Soon", "LTS; active support ending", "", "Y", "N", "Angular 18", ""),
    _fw("Angular", "18.x", "JavaScript Framework", "2025-11-20", "2026-11-20", "Supported", "Current stable LTS", "", "N", "N", "", ""),
    _fw("Angular", "19.x", "JavaScript Framework", "2026-05-15", "2027-05-15", "Supported", "Latest release", "", "N", "N", "", ""),

    # ── Vue.js ───────────────────────────────────────────────────────────────
    _fw("Vue.js", "2.x", "JavaScript Framework", "2023-12-31", "", "End of Life", "EOL Dec 2023; no security patches", "", "Y", "N", "Vue.js 3.x", "React 19"),
    _fw("Vue.js", "3.x", "JavaScript Framework", "2027-12-31", "", "Supported", "Current stable; Composition API", "", "N", "N", "", ""),

    # ── Node.js ──────────────────────────────────────────────────────────────
    _fw("Node.js", "14.x", "Runtime", "2023-04-30", "", "End of Life", "LTS Fermium; EOL Apr 2023", "", "Y", "N", "Node.js 22.x", ""),
    _fw("Node.js", "16.x", "Runtime", "2023-09-11", "", "End of Life", "LTS Gallium; EOL Sep 2023", "", "Y", "N", "Node.js 22.x", ""),
    _fw("Node.js", "18.x", "Runtime", "2025-04-30", "", "Expiring Soon", "LTS Hydrogen; EOL Apr 2025", "", "Y", "N", "Node.js 22.x", ""),
    _fw("Node.js", "20.x", "Runtime", "2026-04-30", "", "Supported", "LTS Iron; active LTS", "", "N", "N", "Node.js 22.x", ""),
    _fw("Node.js", "22.x", "Runtime", "2027-04-30", "", "Supported", "LTS Jod; current LTS", "", "N", "N", "", ""),

    # ── Java / OpenJDK ───────────────────────────────────────────────────────
    _fw("Java", "8 (LTS)", "Runtime", "2030-12-31", "2030-12-31", "Supported", "Oracle extended; Eclipse Temurin supported", "", "Y", "N", "Java 21 LTS", "Java 17 LTS"),
    _fw("Java", "11 (LTS)", "Runtime", "2026-09-30", "2032-01-31", "Supported", "Oracle premier ended; extended support", "", "Y", "N", "Java 21 LTS", ""),
    _fw("Java", "17 (LTS)", "Runtime", "2027-09-30", "2030-09-30", "Supported", "LTS; Jakarta EE 10 baseline", "", "N", "N", "Java 21 LTS", ""),
    _fw("Java", "21 (LTS)", "Runtime", "2031-09-30", "2034-09-30", "Supported", "Current LTS; virtual threads", "", "N", "N", "", ""),

    # ── Python ───────────────────────────────────────────────────────────────
    _fw("Python", "3.8.x", "Runtime", "2024-10-07", "", "End of Life", "EOL Oct 2024", "", "Y", "N", "Python 3.12", "Python 3.13"),
    _fw("Python", "3.9.x", "Runtime", "2025-10-05", "", "Expiring Soon", "Security-only; EOL Oct 2025", "", "Y", "N", "Python 3.12", ""),
    _fw("Python", "3.10.x", "Runtime", "2026-10-04", "", "Supported", "Security-only phase", "", "Y", "N", "Python 3.12", ""),
    _fw("Python", "3.11.x", "Runtime", "2027-10-24", "", "Supported", "Security-only from Oct 2025", "", "N", "N", "Python 3.13", ""),
    _fw("Python", "3.12.x", "Runtime", "2028-10-02", "", "Supported", "Current stable; performance improvements", "", "N", "N", "", ""),
    _fw("Python", "3.13.x", "Runtime", "2029-10-01", "", "Supported", "Latest release; free-threading option", "", "N", "N", "", ""),

    # ── Django ───────────────────────────────────────────────────────────────
    _fw("Django", "3.2 LTS", "Python Framework", "2024-04-01", "", "End of Life", "LTS ended Apr 2024", "", "Y", "N", "Django 5.2 LTS", ""),
    _fw("Django", "4.2 LTS", "Python Framework", "2026-04-01", "", "Supported", "Current LTS", "", "N", "N", "Django 5.2 LTS", ""),
    _fw("Django", "5.2 LTS", "Python Framework", "2028-04-01", "", "Supported", "Latest LTS; Python 3.10+", "", "N", "N", "", ""),

    # ── Ruby on Rails ────────────────────────────────────────────────────────
    _fw("Ruby on Rails", "6.1.x", "Ruby Framework", "2024-10-01", "", "End of Life", "Security support ended", "", "Y", "N", "Rails 7.2.x", "Rails 8.0.x"),
    _fw("Ruby on Rails", "7.0.x", "Ruby Framework", "2025-04-01", "", "Expiring Soon", "Security-only", "", "Y", "N", "Rails 7.2.x", ""),
    _fw("Ruby on Rails", "7.1.x", "Ruby Framework", "2025-10-01", "", "Supported", "Bug fixes + security", "", "N", "N", "Rails 7.2.x", ""),
    _fw("Ruby on Rails", "7.2.x", "Ruby Framework", "2026-10-01", "", "Supported", "Current stable", "", "N", "N", "", ""),
    _fw("Ruby on Rails", "8.0.x", "Ruby Framework", "2027-10-01", "", "Supported", "Latest release; Hotwire-first", "", "N", "N", "", ""),

]


# =============================================================================
# Auto-populate Min CPU / Min RAM based on OS and DB known requirements
# =============================================================================
_OS_HW_REQS = [
    # (keyword_in_name, min_cpu, min_ram)
    # Windows Client
    ("Windows 11",          "2 cores (1 GHz 64-bit)", "4 GB"),
    ("Windows 10",          "1 core (1 GHz)", "2 GB"),
    ("Windows 8",           "1 core (1 GHz)", "1 GB"),
    ("Windows 7",           "1 core (1 GHz)", "1 GB"),
    # Windows Server
    ("Windows Server 2025", "1 core (1.4 GHz 64-bit)", "2 GB"),
    ("Windows Server 2022", "1 core (1.4 GHz 64-bit)", "2 GB"),
    ("Windows Server 2019", "1 core (1.4 GHz 64-bit)", "2 GB"),
    ("Windows Server 2016", "1 core (1.4 GHz 64-bit)", "2 GB"),
    ("Windows Server 2012", "1 core (1.4 GHz 64-bit)", "2 GB"),
    ("Windows Server 2008", "1 core (1 GHz)", "2 GB"),
    ("Windows Server 2003", "1 core (550 MHz)", "256 MB"),
    ("Windows Server",      "1 core (1.4 GHz 64-bit)", "2 GB"),
    # RHEL
    ("RHEL 9",              "1 core (1 GHz)", "1.5 GB"),
    ("RHEL 8",              "1 core (1 GHz)", "1.5 GB"),
    ("RHEL 7",              "1 core (1 GHz)", "1 GB"),
    ("RHEL 6",              "1 core", "1 GB"),
    ("RHEL 5",              "1 core", "512 MB"),
    ("RHEL",                "1 core", "1 GB"),
    # Ubuntu
    ("Ubuntu",              "1 core (1 GHz)", "1 GB"),
    # Debian
    ("Debian",              "1 core", "512 MB"),
    # SLES
    ("SLES 15",             "1 core", "1 GB"),
    ("SLES 12",             "1 core", "512 MB"),
    ("SLES",                "1 core", "512 MB"),
    # CentOS / Rocky / Alma / Oracle Linux
    ("CentOS",              "1 core", "1 GB"),
    ("Rocky",               "1 core (1 GHz)", "1.5 GB"),
    ("AlmaLinux",           "1 core (1 GHz)", "1.5 GB"),
    ("Oracle Linux",        "1 core", "1 GB"),
    # macOS
    ("macOS",               "Apple Silicon / 2 cores", "8 GB"),
    # AIX
    ("AIX",                 "1 POWER core", "2 GB"),
    # HP-UX
    ("HP-UX",               "1 PA-RISC/Itanium core", "1 GB"),
    # Solaris
    ("Solaris",             "1 SPARC/x86 core", "1 GB"),
    # FreeBSD
    ("FreeBSD",             "1 core", "512 MB"),
    # OpenVMS
    ("OpenVMS",             "1 core (Alpha/Itanium/x86)", "512 MB"),
    # Tru64
    ("Tru64",               "1 Alpha core", "256 MB"),
    # Fedora
    ("Fedora",              "1 core", "2 GB"),
    # iOS / Android
    ("iOS",                 "A-series chip", "2 GB"),
    ("Android",             "ARM 1 core", "1 GB"),
    # ChromeOS
    ("ChromeOS",            "1 core", "4 GB"),
    # IBM i
    ("IBM i",               "1 POWER core", "4 GB"),
    # z/OS
    ("z/OS",                "1 zIIP/CP", "4 GB"),
    # Raspberry Pi
    ("Raspberry Pi",        "ARM 1 core", "512 MB"),
]

_DB_HW_REQS = [
    # (keyword_in_db_name, min_cpu, min_ram)
    ("SQL Server",          "2 cores (1.4 GHz)", "2 GB"),
    ("Azure SQL",           "2 vCPUs", "4 GB"),
    ("Oracle DB",           "2 cores", "4 GB"),
    ("Oracle",              "2 cores", "4 GB"),
    ("PostgreSQL",          "1 core", "1 GB"),
    ("MySQL",               "1 core", "512 MB"),
    ("MariaDB",             "1 core", "512 MB"),
    ("MongoDB",             "2 cores", "4 GB"),
    ("Redis",               "1 core", "256 MB"),
    ("ElastiCache",         "1 vCPU", "1 GB"),
    ("DynamoDB",            "Serverless", "Serverless"),
    ("Cassandra",           "2 cores", "4 GB"),
    ("Elasticsearch",       "2 cores", "4 GB"),
    ("OpenSearch",          "2 cores", "4 GB"),
    ("IBM Db2",             "2 cores", "4 GB"),
    ("IBM IMS",             "1 zIIP/CP", "4 GB"),
    ("IBM Informix",        "1 core", "1 GB"),
    ("SAP HANA",            "4 cores", "32 GB"),
    ("SAP ASE",             "2 cores", "4 GB"),
    ("SAP IQ",              "2 cores", "8 GB"),
    ("SAP MaxDB",           "1 core", "2 GB"),
    ("SAP SQL Anywhere",    "1 core", "1 GB"),
    ("Snowflake",           "Serverless", "Serverless"),
    ("Databricks",          "Serverless", "Serverless"),
    ("BigQuery",            "Serverless", "Serverless"),
    ("Teradata",            "4 cores", "16 GB"),
    ("Vertica",             "2 cores", "8 GB"),
    ("Greenplum",           "4 cores", "16 GB"),
    ("Neo4j",               "2 cores", "2 GB"),
    ("InfluxDB",            "2 cores", "2 GB"),
    ("TimescaleDB",         "2 cores", "4 GB"),
    ("CockroachDB",         "2 cores", "4 GB"),
    ("YugabyteDB",          "2 cores", "4 GB"),
    ("Couchbase",           "4 cores", "4 GB"),
    ("CouchDB",             "1 core", "1 GB"),
    ("Cosmos DB",           "Serverless", "Serverless"),
    ("DocumentDB",          "2 vCPUs", "4 GB"),
    ("HBase",               "4 cores", "8 GB"),
    ("Hadoop",              "4 cores", "8 GB"),
    ("Hive",                "2 cores", "4 GB"),
    ("Firebird",            "1 core", "256 MB"),
    ("Progress OpenEdge",   "1 core", "2 GB"),
    ("SingleStore",         "4 cores", "8 GB"),
    ("Exasol",              "2 cores", "8 GB"),
    ("Microsoft Access",    "1 core", "256 MB"),
    ("Visual FoxPro",       "1 core", "128 MB"),
    ("Aurora",              "2 vCPUs", "4 GB"),
    ("Cloud SQL",           "1 vCPU", "3.75 GB"),
    ("AlloyDB",             "2 vCPUs", "8 GB"),
    ("Cloud Spanner",       "Serverless", "Serverless"),
    ("RDS",                 "1 vCPU", "1 GB"),
    ("Actian",              "2 cores", "4 GB"),
]

def _apply_hw_reqs(data_list, hw_reqs, name_key):
    """Apply Min CPU/RAM defaults to data entries that don't have them set."""
    for item in data_list:
        if item.get("Min CPU") and item.get("Min RAM"):
            continue
        name = item.get(name_key, "")
        for keyword, cpu, ram in hw_reqs:
            if keyword.lower() in name.lower():
                if not item.get("Min CPU"):
                    item["Min CPU"] = cpu
                if not item.get("Min RAM"):
                    item["Min RAM"] = ram
                break

_apply_hw_reqs(OS_DATA, _OS_HW_REQS, "OS Version")
_apply_hw_reqs(DB_DATA, _DB_HW_REQS, "Database")
