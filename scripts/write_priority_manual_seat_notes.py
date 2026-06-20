"""One-off helper: write priority constituency manual seat notes and run merge."""

from __future__ import annotations

import pandas as pd

from src.seat_analysis.common import MANUAL_NOTES_PATH, ensure_dirs
from src.seat_analysis.merge_manual_seat_notes import main as merge_main

SOURCE_NOTES = (
    "Based on 2019/2024 election results, The 543 constituency data, "
    "and public political context."
)
REVIEWED = "2026-06-14"

ROWS = [
    {
        "state": "Uttar Pradesh",
        "constituency": "Varanasi",
        "state_key": "UTTAR PRADESH",
        "constituency_key": "VARANASI",
        "manual_summary": (
            "Varanasi is Narendra Modi's constituency and one of India's most "
            "symbolically loaded seats. BJP retained it in 2024, but any shift in "
            "margin or vote share here is read as a national signal, not just a local result."
        ),
        "manual_electoral_movement": (
            "Varanasi remained with the BJP in 2024, but the seat is more important "
            "than a normal retained seat because it is Narendra Modi's constituency. "
            "Any movement in margin or vote share here carries symbolic weight beyond "
            "the seat itself."
        ),
        "manual_key_factors": (
            "candidate profile;local context;state mood;"
            "prime ministerial candidate effect;urban visibility;organisational depth;"
            "symbolic politics of Kashi;opposition consolidation"
        ),
        "manual_local_context": (
            "Why it mattered: This is the BJP's national-leadership seat. Varanasi is "
            "not just a constituency; it is a political stage for the Modi model of "
            "governance, Hindutva symbolism, infrastructure visibility, and nationalised "
            "campaigning. Factors that may have mattered: The BJP's strength here likely "
            "rests on the prime ministerial candidate effect, urban visibility, "
            "organisational depth, and the symbolic politics of Kashi. If the margin "
            "narrowed in your data, frame it as opposition consolidation rather than "
            "evidence of structural BJP weakness."
        ),
        "manual_what_to_watch": (
            "Whether Varanasi remains a pure leadership seat or begins showing signs "
            "of normal anti-incumbency once the election is less presidential."
        ),
    },
    {
        "state": "Kerala",
        "constituency": "Wayanad",
        "state_key": "KERALA",
        "constituency_key": "WAYANAD",
        "manual_summary": (
            "Wayanad is Congress's southern safe harbour and a Gandhi-family reserve "
            "seat. Rahul Gandhi won here in 2024 before retaining Rae Bareli and "
            "vacating the seat for Priyanka Gandhi Vadra's parliamentary entry."
        ),
        "manual_electoral_movement": (
            "Wayanad remained a Congress stronghold. Rahul Gandhi won the seat in the "
            "2024 general election and later retained Rae Bareli, vacating Wayanad; "
            "the seat then became the site of Priyanka Gandhi Vadra's parliamentary entry."
        ),
        "manual_key_factors": (
            "candidate profile;alliance arithmetic;local context;state mood;"
            "Congress local alliance structure;Kerala anti-BJP pattern;"
            "Gandhi family national visibility"
        ),
        "manual_local_context": (
            "Why it mattered: Wayanad functions as Congress's southern safe harbour. "
            "It reflects the party's resilience in Kerala and its dependence on seats "
            "where minority, anti-BJP, and Congress-aligned voters remain strongly "
            "consolidated. Factors that may have mattered: The seat's political profile "
            "is shaped by Congress's local alliance structure, Kerala's anti-BJP electoral "
            "pattern, and the Gandhi family's national visibility. It should not be read "
            "as a competitive BJP expansion seat."
        ),
        "manual_what_to_watch": (
            "Whether Wayanad remains a Gandhi-family reserve seat or becomes a deeper "
            "test of Congress's ability to convert symbolic leadership into durable organisation."
        ),
    },
    {
        "state": "Uttar Pradesh",
        "constituency": "Rae Bareli",
        "state_key": "UTTAR PRADESH",
        "constituency_key": "RAE BARELI",
        "manual_summary": (
            "Rae Bareli is a historic Gandhi-family anchor in North India and central "
            "to Congress's 2024 revival narrative. Rahul Gandhi's decision to retain "
            "this seat over Wayanad gave it renewed national importance."
        ),
        "manual_electoral_movement": (
            "Rae Bareli remained central to Congress's 2024 revival story. Rahul Gandhi's "
            "decision to retain Rae Bareli over Wayanad gave the seat renewed national importance."
        ),
        "manual_key_factors": (
            "candidate profile;alliance arithmetic;local context;state mood;"
            "family legacy;opposition consolidation;local Congress memory;"
            "SP-Congress alliance environment"
        ),
        "manual_local_context": (
            "Why it mattered: This is one of the historic anchors of the Gandhi family "
            "in North India. In 2024, it mattered not only as a Congress win but as a "
            "statement that the party wanted to re-enter the Hindi heartland fight. "
            "Factors that may have mattered: Family legacy, opposition consolidation, "
            "local Congress memory, and the Samajwadi Party-Congress alliance environment "
            "likely mattered. This seat should be read as both symbolic and strategic."
        ),
        "manual_what_to_watch": (
            "Whether Rae Bareli becomes a base for Congress rebuilding in Uttar Pradesh "
            "or remains an exceptional legacy seat."
        ),
    },
    {
        "state": "Uttar Pradesh",
        "constituency": "Amethi",
        "state_key": "UTTAR PRADESH",
        "constituency_key": "AMETHI",
        "manual_summary": (
            "Amethi was one of the most symbolically important Congress comeback seats "
            "after the BJP's 2019 breakthrough there, representing recovery of a lost "
            "family bastion."
        ),
        "manual_electoral_movement": (
            "Amethi was one of the most symbolically important Congress comeback seats "
            "after the BJP's 2019 breakthrough there."
        ),
        "manual_key_factors": (
            "candidate profile;alliance arithmetic;turnout;local context;"
            "candidate selection;local anti-incumbency;residual Congress organisation"
        ),
        "manual_local_context": (
            "Why it mattered: For Congress, Amethi represented the recovery of a lost "
            "family bastion. For the BJP, losing it weakened one of the party's strongest "
            "2019 symbolic victories. Factors that may have mattered: Candidate selection, "
            "local anti-incumbency, residual Congress organisation, and alliance arithmetic "
            "likely mattered more than a simple national swing explanation."
        ),
        "manual_what_to_watch": (
            "Whether Congress can rebuild Amethi as an organisation-led seat, or whether "
            "the result was mainly a one-cycle correction against the sitting BJP profile."
        ),
    },
    {
        "state": "Gujarat",
        "constituency": "Gandhinagar",
        "state_key": "GUJARAT",
        "constituency_key": "GANDHINAGAR",
        "manual_summary": (
            "Gandhinagar is one of the BJP's safest high-command seats, associated with "
            "national leadership and the party's organisational core in Gujarat."
        ),
        "manual_electoral_movement": (
            "Gandhinagar remained one of the BJP's safest high-command seats."
        ),
        "manual_key_factors": (
            "candidate profile;local context;state mood;"
            "BJP organisational depth;Gujarat party alignment;"
            "urban/suburban middle-class consolidation;leadership effects"
        ),
        "manual_local_context": (
            "Why it mattered: The seat is associated with the BJP's national leadership "
            "and organisational core. It is less useful as a competitive-seat indicator "
            "and more useful as a benchmark of the party's command over Gujarat. "
            "Factors that may have mattered: BJP organisational depth, Gujarat's "
            "long-running party alignment, urban/suburban middle-class consolidation, "
            "and leadership effects."
        ),
        "manual_what_to_watch": (
            "Not whether BJP wins, but whether margins stay overwhelming or slowly "
            "normalise over time."
        ),
    },
    {
        "state": "Maharashtra",
        "constituency": "Nagpur",
        "state_key": "MAHARASHTRA",
        "constituency_key": "NAGPUR",
        "manual_summary": (
            "Nagpur carries symbolic weight beyond Maharashtra because of the RSS "
            "presence and Nitin Gadkari's profile, tying the seat to the BJP's "
            "ideological and organisational ecosystem."
        ),
        "manual_electoral_movement": (
            "Nagpur remained politically important because it is tied to the BJP's "
            "ideological and organisational ecosystem."
        ),
        "manual_key_factors": (
            "candidate profile;alliance arithmetic;local context;state mood;"
            "candidate reputation;BJP organisation;urban development politics;"
            "Maharashtra alliance environment"
        ),
        "manual_local_context": (
            "Why it mattered: Nagpur is not just another Maharashtra seat. It carries "
            "symbolic significance because of the RSS presence and the profile of Nitin "
            "Gadkari. Factors that may have mattered: Candidate reputation, BJP "
            "organisation, urban development politics, and Maharashtra's shifting alliance "
            "environment all matter here."
        ),
        "manual_what_to_watch": (
            "Whether Nagpur continues to behave as a candidate-strength seat or becomes "
            "more exposed to Maharashtra-level volatility."
        ),
    },
    {
        "state": "Telangana",
        "constituency": "Hyderabad",
        "state_key": "TELANGANA",
        "constituency_key": "HYDERABAD",
        "manual_summary": (
            "Hyderabad tests whether BJP national ambition can break into a "
            "minority-concentrated urban fortress dominated by AIMIM, making it unlike "
            "a standard BJP-versus-Congress contest."
        ),
        "manual_electoral_movement": (
            "Hyderabad remained a seat where the BJP's national ambition confronts a "
            "strong local political structure."
        ),
        "manual_key_factors": (
            "candidate profile;local context;turnout;"
            "religious composition;local party networks;candidate identity;urban polarisation"
        ),
        "manual_local_context": (
            "Why it mattered: The seat is important because it tests whether the BJP can "
            "break into a minority-concentrated urban fortress dominated by AIMIM. "
            "Factors that may have mattered: Religious composition, local party networks, "
            "candidate identity, and urban polarisation are central. This is not a normal "
            "BJP-versus-Congress seat."
        ),
        "manual_what_to_watch": (
            "Whether BJP growth in Telangana translates into actual seat conversion in "
            "Hyderabad, or whether AIMIM's local structure remains too strong."
        ),
    },
    {
        "state": "West Bengal",
        "constituency": "Asansol",
        "state_key": "WEST BENGAL",
        "constituency_key": "ASANSOL",
        "manual_summary": (
            "Asansol is a high-interest West Bengal urban-industrial seat where intense "
            "BJP-TMC competition tests whether BJP strength can hold in working-class "
            "and migrant-heavy urban zones."
        ),
        "manual_electoral_movement": (
            "Asansol is one of the more interesting West Bengal urban-industrial seats "
            "because it has seen intense BJP-TMC competition."
        ),
        "manual_key_factors": (
            "candidate profile;alliance arithmetic;local context;state mood;"
            "TMC organisation;BJP non-Bengali voter appeal;"
            "labour/industrial identity;anti-incumbency dynamics"
        ),
        "manual_local_context": (
            "Why it mattered: It is a test of whether BJP strength in Bengal can hold "
            "in urban/industrial zones where Hindi-speaking, working-class, and migrant "
            "communities matter alongside Bengali regional politics. Factors that may "
            "have mattered: TMC organisation, BJP's non-Bengali voter appeal, "
            "labour/industrial identity, candidate profile, and anti-incumbency dynamics."
        ),
        "manual_what_to_watch": (
            "Whether Asansol remains a BJP-opportunity seat or settles into TMC's "
            "broader Bengal dominance."
        ),
    },
    {
        "state": "West Bengal",
        "constituency": "Diamond harbour",
        "state_key": "WEST BENGAL",
        "constituency_key": "DIAMOND HARBOUR",
        "manual_summary": (
            "Diamond Harbour is a highly symbolic TMC power-centre seat tied to "
            "Abhishek Banerjee and next-generation Trinamool leadership in South Bengal."
        ),
        "manual_electoral_movement": (
            "Diamond Harbour remained a highly symbolic TMC seat because of Abhishek Banerjee."
        ),
        "manual_key_factors": (
            "candidate profile;local context;state mood;"
            "TMC local machinery;Abhishek Banerjee profile;"
            "welfare delivery networks;BJP seat-conversion difficulty"
        ),
        "manual_local_context": (
            "Why it mattered: This is not just a South Bengal constituency. It is a "
            "power-centre seat for the next-generation leadership of the Trinamool Congress. "
            "Factors that may have mattered: TMC's local machinery, Abhishek Banerjee's "
            "profile, welfare delivery networks, and the BJP's difficulty converting Bengal "
            "vote share into seats in TMC strongholds."
        ),
        "manual_what_to_watch": (
            "Whether Diamond Harbour continues to function as a TMC fortress or whether "
            "BJP can make future contests more competitive."
        ),
    },
    {
        "state": "Maharashtra",
        "constituency": "Baramati",
        "state_key": "MAHARASHTRA",
        "constituency_key": "BARAMATI",
        "manual_summary": (
            "Baramati was one of Maharashtra's most watched contests because it reflected "
            "the split in the NCP family and organisation, making it a battle over "
            "political legacy as much as party labels."
        ),
        "manual_electoral_movement": (
            "Baramati was one of the most politically watched contests in Maharashtra "
            "because it reflected the split in the NCP family and organisation."
        ),
        "manual_key_factors": (
            "candidate profile;alliance arithmetic;local context;state mood;"
            "family networks;local patronage;NCP factional loyalty;"
            "candidate credibility;Maharashtra fragmented alliance politics"
        ),
        "manual_local_context": (
            "Why it mattered: This seat was less about a normal party contest and more "
            "about control of a political legacy. Factors that may have mattered: Family "
            "networks, local patronage, NCP factional loyalty, candidate credibility, and "
            "Maharashtra's fragmented alliance politics."
        ),
        "manual_what_to_watch": (
            "Whether the result settles the Pawar-family question locally or whether "
            "Baramati remains a factional battleground."
        ),
    },
    {
        "state": "Kerala",
        "constituency": "Thiruvananthapuram",
        "state_key": "KERALA",
        "constituency_key": "THIRUVANANTHAPURAM",
        "manual_summary": (
            "Thiruvananthapuram is one of the BJP's most important southern target seats, "
            "testing whether the party can become competitive in a high-literacy, urban, "
            "non-Hindi state."
        ),
        "manual_electoral_movement": (
            "Thiruvananthapuram remained one of the BJP's most important southern target seats."
        ),
        "manual_key_factors": (
            "candidate profile;alliance arithmetic;local context;state mood;"
            "urban middle-class voters;minority consolidation;Congress strength;"
            "Kerala anti-BJP political structure"
        ),
        "manual_local_context": (
            "Why it mattered: It is a rare Kerala constituency where the BJP has repeatedly "
            "tried to become competitive. The seat tests whether the party can grow in "
            "high-literacy, urban, non-Hindi states. Factors that may have mattered: "
            "Candidate profile, urban middle-class voters, minority consolidation, Congress "
            "strength, and Kerala's broader anti-BJP political structure."
        ),
        "manual_what_to_watch": (
            "Whether BJP's Kerala strategy remains vote-share growth without seat conversion, "
            "or whether Thiruvananthapuram eventually becomes the breakthrough."
        ),
    },
    {
        "state": "Tamil Nadu",
        "constituency": "COIMBATORE",
        "state_key": "TAMIL NADU",
        "constituency_key": "COIMBATORE",
        "manual_summary": (
            "Coimbatore was framed as one of the BJP's key entry points into Tamil Nadu, "
            "testing whether the party can build a serious southern urban-industrial base "
            "outside its traditional geographies."
        ),
        "manual_electoral_movement": (
            "Coimbatore was framed as one of the BJP's key entry points into Tamil Nadu."
        ),
        "manual_key_factors": (
            "candidate profile;local context;state mood;"
            "urbanisation;industrial economy;Hindutva mobilisation;"
            "candidate visibility;Dravidian party networks"
        ),
        "manual_local_context": (
            "Why it mattered: The seat is important because it tests whether the BJP can "
            "build a serious southern urban-industrial base outside its traditional "
            "geographies. Factors that may have mattered: Urbanisation, industrial economy, "
            "Hindutva mobilisation, candidate visibility, and the strength of Dravidian "
            "party networks."
        ),
        "manual_what_to_watch": (
            "Whether BJP's Coimbatore performance becomes the foundation for future Tamil "
            "Nadu growth or remains a high-noise, low-conversion experiment."
        ),
    },
    {
        "state": "Karnataka",
        "constituency": "Bangalore South",
        "state_key": "KARNATAKA",
        "constituency_key": "BANGALORE SOUTH",
        "manual_summary": (
            "Bangalore South is a high-profile urban BJP seat representing the party's "
            "appeal among educated, middle-class, and aspirational voters in a major "
            "technology-driven city."
        ),
        "manual_electoral_movement": (
            "Bangalore South remained a high-profile urban BJP seat."
        ),
        "manual_key_factors": (
            "candidate profile;local context;state mood;"
            "urban ideology;national leadership preference;"
            "middle-class politics;Bengaluru development pressures"
        ),
        "manual_local_context": (
            "Why it mattered: It represents the BJP's appeal among urban, educated, "
            "middle-class, and aspirational voters in a major technology-driven city. "
            "Factors that may have mattered: Urban ideology, candidate profile, national "
            "leadership preference, middle-class politics, and Bengaluru's development pressures."
        ),
        "manual_what_to_watch": (
            "Whether urban governance dissatisfaction weakens BJP margins, or whether "
            "national identity and middle-class consolidation continue to dominate."
        ),
    },
    {
        "state": "Maharashtra",
        "constituency": "Mumbai North",
        "state_key": "MAHARASHTRA",
        "constituency_key": "MUMBAI NORTH",
        "manual_summary": (
            "Mumbai North is an urban seat where candidate strength, party alliances, and "
            "urban class composition matter heavily, reflecting the BJP-Shiv Sena alliance's "
            "hold on affluent and suburban Mumbai."
        ),
        "manual_electoral_movement": (
            "Mumbai North should be treated as a Mumbai urban seat where candidate strength, "
            "party alliances, and urban class composition matter heavily."
        ),
        "manual_key_factors": (
            "candidate profile;alliance arithmetic;local context;state mood;"
            "urban voter consolidation;candidate visibility;"
            "Marathi versus non-Marathi voter dynamics;Maharashtra alliance split"
        ),
        "manual_local_context": (
            "Why it mattered: It reflects the BJP/Shiv Sena alliance's ability to hold "
            "affluent and suburban Mumbai spaces. Factors that may have mattered: Urban "
            "voter consolidation, candidate visibility, Marathi versus non-Marathi voter "
            "dynamics, and the Maharashtra alliance split."
        ),
        "manual_what_to_watch": (
            "Whether Mumbai's seats continue to align with national-party politics or "
            "fragment around state-level alliance changes."
        ),
    },
    {
        "state": "Maharashtra",
        "constituency": "Mumbai South",
        "state_key": "MAHARASHTRA",
        "constituency_key": "MUMBAI SOUTH",
        "manual_summary": (
            "Mumbai South is an elite, commercial urban seat capturing the politics of "
            "old Mumbai, business interests, and the post-split Shiv Sena landscape."
        ),
        "manual_electoral_movement": (
            "Mumbai South is a different kind of urban seat: elite, commercial, and "
            "politically symbolic."
        ),
        "manual_key_factors": (
            "candidate profile;alliance arithmetic;local context;state mood;"
            "class composition;local candidate networks;Sena factional identity;"
            "Congress/NCP alliance arithmetic;urban issue salience"
        ),
        "manual_local_context": (
            "Why it mattered: It captures the politics of old Mumbai, business interests, "
            "urban governance, and the post-split Shiv Sena landscape. Factors that may "
            "have mattered: Class composition, local candidate networks, Sena factional "
            "identity, Congress/NCP alliance arithmetic, and urban issue salience."
        ),
        "manual_what_to_watch": (
            "Whether Mumbai South remains personality/alliance-driven or becomes more "
            "clearly aligned with national bloc politics."
        ),
    },
    {
        "state": "Uttar Pradesh",
        "constituency": "Kannauj",
        "state_key": "UTTAR PRADESH",
        "constituency_key": "KANNAUJ",
        "manual_summary": (
            "Kannauj returned to the centre of Uttar Pradesh politics through Akhilesh "
            "Yadav's profile and the SP's 2024 recovery, testing Samajwadi Party revival "
            "in its old heartland."
        ),
        "manual_electoral_movement": (
            "Kannauj returned to the centre of Uttar Pradesh politics because of Akhilesh "
            "Yadav's profile and the SP's 2024 recovery."
        ),
        "manual_key_factors": (
            "candidate profile;alliance arithmetic;turnout;local context;state mood;"
            "Yadav-Muslim consolidation;SP-Congress alliance arithmetic;"
            "anti-BJP mobilisation"
        ),
        "manual_local_context": (
            "Why it mattered: This seat is a test of Samajwadi Party revival in its old "
            "heartland. Factors that may have mattered: Yadav-Muslim consolidation, "
            "SP-Congress alliance arithmetic, local candidate profile, and anti-BJP mobilisation."
        ),
        "manual_what_to_watch": (
            "Whether Kannauj signals durable SP recovery or simply a leader-specific consolidation."
        ),
    },
    {
        "state": "Uttar Pradesh",
        "constituency": "Faizabad",
        "state_key": "UTTAR PRADESH",
        "constituency_key": "FAIZABAD",
        "manual_summary": (
            "Faizabad was one of the most symbolically powerful results of 2024 because "
            "of its connection to Ayodhya, challenging assumptions that religious symbolism "
            "alone guarantees electoral security."
        ),
        "manual_electoral_movement": (
            "Faizabad was one of the most symbolically powerful results of 2024 because "
            "of its connection to Ayodhya."
        ),
        "manual_key_factors": (
            "candidate profile;alliance arithmetic;turnout;local context;state mood;"
            "local caste arithmetic;candidate selection;development displacement concerns;"
            "opposition consolidation;national symbolism versus local grievances"
        ),
        "manual_local_context": (
            "Why it mattered: If a seat tied to Ayodhya becomes competitive or flips, it "
            "challenges the assumption that religious symbolism alone guarantees electoral "
            "security. Factors that may have mattered: Local caste arithmetic, candidate "
            "selection, development displacement concerns, opposition consolidation, and the "
            "gap between national symbolism and local grievances."
        ),
        "manual_what_to_watch": (
            "Whether Faizabad remains an opposition breakthrough or returns to BJP under "
            "different candidate/local conditions."
        ),
    },
    {
        "state": "Uttar Pradesh",
        "constituency": "Sultanpur",
        "state_key": "UTTAR PRADESH",
        "constituency_key": "SULTANPUR",
        "manual_summary": (
            "Sultanpur is a competitive Uttar Pradesh seat useful for understanding "
            "whether BJP's UP losses were isolated or part of a wider shift in "
            "eastern/central UP."
        ),
        "manual_electoral_movement": (
            "Sultanpur should be analysed as a competitive Uttar Pradesh seat where "
            "candidate profile and alliance arithmetic matter."
        ),
        "manual_key_factors": (
            "candidate profile;alliance arithmetic;turnout;local context;state mood;"
            "caste mobilisation;local candidate reputation;SP-Congress coordination"
        ),
        "manual_local_context": (
            "Why it mattered: It is useful for understanding whether the BJP's UP losses "
            "were isolated or part of a wider shift in eastern/central UP. Factors that "
            "may have mattered: Caste mobilisation, local candidate reputation, SP-Congress "
            "coordination, and turnout."
        ),
        "manual_what_to_watch": (
            "Whether BJP recovers through candidate replacement/organisation or whether "
            "the opposition consolidates further."
        ),
    },
    {
        "state": "Uttar Pradesh",
        "constituency": "Kairana",
        "state_key": "UTTAR PRADESH",
        "constituency_key": "KAIRANA",
        "manual_summary": (
            "Kairana is an important western UP seat with a history of polarisation and "
            "alliance politics, testing whether BJP polarisation remains dominant or "
            "caste-community alliances can counter it."
        ),
        "manual_electoral_movement": (
            "Kairana is an important western UP seat with a history of polarisation and "
            "alliance politics."
        ),
        "manual_key_factors": (
            "candidate profile;alliance arithmetic;turnout;local context;state mood;"
            "Jat-Muslim dynamics;SP/RLD/BJP alliance shifts;candidate selection;"
            "local communal history"
        ),
        "manual_local_context": (
            "Why it mattered: It tests whether BJP polarisation politics remains dominant "
            "in western UP or whether caste-community alliances can counter it. Factors "
            "that may have mattered: Jat-Muslim dynamics, SP/RLD/BJP alliance shifts, "
            "candidate selection, and local communal history."
        ),
        "manual_what_to_watch": (
            "Whether the BJP's western UP coalition stabilises or opposition/regional "
            "alignments reopen the seat."
        ),
    },
    {
        "state": "West Bengal",
        "constituency": "Jadavpur",
        "state_key": "WEST BENGAL",
        "constituency_key": "JADAVPUR",
        "manual_summary": (
            "Jadavpur is a politically expressive Kolkata-area seat useful for understanding "
            "urban Bengal politics where ideology, students, middle-class voters, and TMC "
            "organisational strength interact."
        ),
        "manual_electoral_movement": (
            "Jadavpur remained important as a politically expressive Kolkata-area seat."
        ),
        "manual_key_factors": (
            "candidate profile;local context;state mood;"
            "TMC urban organisation;anti-BJP consolidation;"
            "Left/Congress fragmentation;local candidate appeal"
        ),
        "manual_local_context": (
            "Why it mattered: The seat is useful for understanding urban Bengal politics, "
            "where ideology, students, middle-class voters, and TMC organisational strength "
            "all interact. Factors that may have mattered: TMC's urban organisation, "
            "anti-BJP consolidation, Left/Congress weakness or fragmentation, and local "
            "candidate appeal."
        ),
        "manual_what_to_watch": (
            "Whether BJP can grow in Kolkata-adjacent seats or remains blocked by TMC's "
            "urban machine."
        ),
    },
    {
        "state": "West Bengal",
        "constituency": "Tamluk",
        "state_key": "WEST BENGAL",
        "constituency_key": "TAMLUK",
        "manual_summary": (
            "Tamluk is a high-interest Bengal seat with a history of anti-Left politics "
            "and later BJP/TMC competition, helping show whether BJP growth is concentrated "
            "in specific sub-regions."
        ),
        "manual_electoral_movement": (
            "Tamluk is a high-interest Bengal seat because of its history with anti-Left "
            "politics and later BJP/TMC competition."
        ),
        "manual_key_factors": (
            "candidate profile;local context;state mood;"
            "local organisational strength;Medinipur-region political networks;"
            "TMC-BJP polarisation"
        ),
        "manual_local_context": (
            "Why it mattered: It helps show whether BJP's Bengal growth is concentrated "
            "in specific sub-regions rather than uniform across the state. Factors that "
            "may have mattered: Local organisational strength, candidate profile, "
            "Medinipur-region political networks, and TMC-BJP polarisation."
        ),
        "manual_what_to_watch": (
            "Whether Tamluk becomes a durable BJP foothold or swings with Bengal's "
            "broader state mood."
        ),
    },
    {
        "state": "West Bengal",
        "constituency": "Dum dum",
        "state_key": "WEST BENGAL",
        "constituency_key": "DUM DUM",
        "manual_summary": (
            "Dum Dum is a dense urban/suburban Bengal seat where TMC strength has been "
            "difficult for BJP to break, capturing the challenge BJP faces in "
            "Kolkata-adjacent constituencies."
        ),
        "manual_electoral_movement": (
            "Dum Dum is a dense urban/suburban Bengal seat where TMC strength has been "
            "difficult for BJP to break."
        ),
        "manual_key_factors": (
            "candidate profile;local context;turnout;state mood;"
            "urban working-class networks;TMC organisation;"
            "minority/local consolidation;opposition fragmentation"
        ),
        "manual_local_context": (
            "Why it mattered: It captures the challenge BJP faces in Kolkata-adjacent "
            "constituencies despite statewide vote-share ambitions. Factors that may have "
            "mattered: Urban working-class networks, TMC organisation, minority/local "
            "consolidation, and opposition fragmentation."
        ),
        "manual_what_to_watch": (
            "Whether BJP's Bengal ceiling is lower in metropolitan seats than in northern "
            "or western Bengal."
        ),
    },
    {
        "state": "Madhya Pradesh",
        "constituency": "Chhindwara",
        "state_key": "MADHYA PRADESH",
        "constituency_key": "CHHINDWARA",
        "manual_summary": (
            "Chhindwara is one of the most important Congress legacy seats in Madhya Pradesh, "
            "long associated with Kamal Nath's political base. A BJP breakthrough here would "
            "signal weakening of a regional Congress fortress."
        ),
        "manual_electoral_movement": (
            "Chhindwara is one of the most important Congress legacy seats in Madhya Pradesh."
        ),
        "manual_key_factors": (
            "candidate profile;local context;state mood;"
            "local networks;candidate inheritance;BJP statewide dominance;"
            "Congress organisational erosion"
        ),
        "manual_local_context": (
            "Why it mattered: It has long been associated with Kamal Nath's political base. "
            "Any BJP breakthrough here would represent not just a seat gain but the weakening "
            "of a Congress regional fortress. Factors that may have mattered: Local networks, "
            "candidate inheritance, BJP's statewide dominance, and Congress organisational erosion."
        ),
        "manual_what_to_watch": (
            "Whether Congress can retain regional strongholds in BJP-dominant states, or "
            "whether even legacy seats become vulnerable."
        ),
    },
    {
        "state": "Himachal Pradesh",
        "constituency": "MANDI",
        "state_key": "HIMACHAL PRADESH",
        "constituency_key": "MANDI",
        "manual_summary": (
            "Mandi became a high-profile Himachal seat where celebrity, party organisation, "
            "and state-level political mood intersect, testing whether it behaves as a "
            "BJP-safe seat or grows more competitive."
        ),
        "manual_electoral_movement": (
            "Mandi became a high-profile Himachal seat because of candidate visibility "
            "and BJP's strength in the state."
        ),
        "manual_key_factors": (
            "candidate profile;local context;state mood;"
            "candidate recognition;BJP Himachal organisation;local identity;"
            "Congress state government performance"
        ),
        "manual_local_context": (
            "Why it mattered: It is a seat where celebrity, party organisation, and "
            "state-level political mood intersect. Factors that may have mattered: "
            "Candidate recognition, BJP's Himachal organisation, local identity, and the "
            "Congress state government's performance."
        ),
        "manual_what_to_watch": (
            "Whether Mandi behaves like a BJP-safe seat or becomes more competitive "
            "under state anti-incumbency."
        ),
    },
    {
        "state": "West Bengal",
        "constituency": "Kolkata Dakshin",
        "state_key": "WEST BENGAL",
        "constituency_key": "KOLKATA DAKSHIN",
        "manual_summary": (
            "Kolkata Dakshin is a key TMC urban seat reflecting the party's hold over "
            "Kolkata's political imagination and the difficulty BJP faces breaking into "
            "the city core."
        ),
        "manual_electoral_movement": (
            "Kolkata Dakshin remains a key TMC urban seat."
        ),
        "manual_key_factors": (
            "candidate profile;local context;state mood;"
            "urban Bengali identity;TMC welfare networks;"
            "candidate familiarity;anti-BJP consolidation"
        ),
        "manual_local_context": (
            "Why it mattered: It reflects the TMC's hold over Kolkata's political imagination "
            "and the difficulty BJP faces in breaking into the city's core constituencies. "
            "Factors that may have mattered: Urban Bengali identity, TMC welfare networks, "
            "candidate familiarity, and anti-BJP consolidation."
        ),
        "manual_what_to_watch": (
            "Whether BJP's Bengal strategy can penetrate Kolkata proper, or whether its "
            "future growth remains outside the city core."
        ),
    },
]


def main() -> None:
    ensure_dirs()
    for row in ROWS:
        row["manual_confidence"] = "medium"
        row["manual_demographic_context"] = ""
        row["analyst_name"] = "manual review"
        row["last_reviewed"] = REVIEWED
        row["source_notes"] = SOURCE_NOTES

    df = pd.DataFrame(
        ROWS,
        columns=[
            "state",
            "constituency",
            "state_key",
            "constituency_key",
            "manual_summary",
            "manual_electoral_movement",
            "manual_key_factors",
            "manual_demographic_context",
            "manual_local_context",
            "manual_what_to_watch",
            "manual_confidence",
            "analyst_name",
            "last_reviewed",
            "source_notes",
        ],
    )
    df.to_csv(MANUAL_NOTES_PATH, index=False)
    print(f"Wrote {len(df)} manual seat notes to {MANUAL_NOTES_PATH}")
    merge_main()


if __name__ == "__main__":
    main()
