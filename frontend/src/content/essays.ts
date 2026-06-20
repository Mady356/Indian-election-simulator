export type Essay = {
  slug: string;
  series: string;
  title: string;
  subtitle: string;
  dek: string;
  date: string;
  readTime: string;
  tags: string[];
  featuredConstituencies?: {
    name: string;
    state: string;
    stateKey: string;
    constituencyKey: string;
    note: string;
  }[];
  sections: {
    heading?: string;
    body: string[];
  }[];
};

export const ESSAYS: Essay[] = [
  {
    slug: "india-urban-bjp-exception",
    series: "The India Exception",
    title: "Why India’s Right-Wing Party Flips the Script in Urban India",
    subtitle: "The India Exception, Part I",
    dek: "In many democracies, cities are where the right goes to lose. In India, urbanisation can strengthen the BJP’s politics of aspiration, order, development, and national identity.",
    date: "2026-06-20",
    readTime: "8 min read",
    tags: [
      "urban India",
      "BJP",
      "political geography",
      "Lok Sabha",
      "electoral behaviour",
    ],
    featuredConstituencies: [
      {
        name: "Bangalore South",
        state: "Karnataka",
        stateKey: "KARNATAKA",
        constituencyKey: "BANGALORE SOUTH",
        note: "A high-profile urban BJP seat where aspirational, educated, middle-class voters meet national leadership preference.",
      },
      {
        name: "Mumbai North",
        state: "Maharashtra",
        stateKey: "MAHARASHTRA",
        constituencyKey: "MUMBAI NORTH",
        note: "Affluent and suburban Mumbai where candidate strength, alliances, and urban class composition shape outcomes.",
      },
      {
        name: "Varanasi",
        state: "Uttar Pradesh",
        stateKey: "UTTAR PRADESH",
        constituencyKey: "VARANASI",
        note: "A national leadership seat where infrastructure visibility and presidentialised politics carry symbolic weight.",
      },
      {
        name: "Nagpur",
        state: "Maharashtra",
        stateKey: "MAHARASHTRA",
        constituencyKey: "NAGPUR",
        note: "Urban development politics intersect with the BJP’s ideological and organisational ecosystem.",
      },
      {
        name: "Gandhinagar",
        state: "Gujarat",
        stateKey: "GUJARAT",
        constituencyKey: "GANDHINAGAR",
        note: "A BJP high-command benchmark — less a competitive indicator than a measure of Gujarat command.",
      },
      {
        name: "COIMBATORE",
        state: "Tamil Nadu",
        stateKey: "TAMIL NADU",
        constituencyKey: "COIMBATORE",
        note: "Framed as a BJP entry point, but Dravidian party networks limit seat conversion despite vote-share growth.",
      },
      {
        name: "Hyderabad",
        state: "Telangana",
        stateKey: "TELANGANA",
        constituencyKey: "HYDERABAD",
        note: "A minority-concentrated urban fortress where AIMIM’s local structure resists standard BJP-versus-Congress framing.",
      },
      {
        name: "Kolkata Dakshin",
        state: "West Bengal",
        stateKey: "WEST BENGAL",
        constituencyKey: "KOLKATA DAKSHIN",
        note: "A TMC urban stronghold where Bengali regional identity and anti-BJP consolidation block BJP penetration.",
      },
    ],
    sections: [
      {
        body: [
          "In much of the world, cities are expected to lean left.",
          "In the United States, even deeply Republican states often contain Democratic cities. Rural California can vote Republican, while cities in Texas, Georgia, or Arizona can vote Democratic. The standard explanation is simple: cities are younger, more diverse, more educated, more multicultural, and therefore more progressive.",
          "But India complicates that story.",
          "The world’s largest democracy often flips this script. India’s preeminent right-wing party, the BJP, has repeatedly shown strength in major urban and semi-urban constituencies. Delhi, Mumbai, Bengaluru, Ahmedabad, Surat, Nagpur, Varanasi, and many other visible urban spaces have not behaved like automatic anti-right bastions. In fact, many of them have become central to the BJP’s national coalition.",
          "So the question is obvious: why?",
          "Are Indian cities old, monolithic, and conservative? Anyone who has walked through Delhi, Mumbai, Bengaluru, Hyderabad, or Pune knows that answer is too simple. These are young, crowded, aspirational, messy, diverse, unequal, hyper-modern places. They are not culturally frozen spaces.",
          "The better answer is that India’s urban politics is not organised around the same social categories as American or European urban politics.",
          "In the West, cities often become engines of liberal politics because urban voters are reacting against older national, religious, or ethnic majoritarian identities. In India, urbanisation can do the opposite. For many voters, the city does not weaken national identity; it strengthens it. The city is where aspiration, state capacity, infrastructure, security, welfare delivery, Hindu identity, and middle-class nationalism often meet.",
          "That is the India exception.",
          "The BJP does not simply win urban India because cities are “conservative.” It wins many urban seats because it has successfully presented itself as the party of aspiration, order, delivery, national pride, and upward mobility.",
        ],
      },
      {
        heading: "The BJP’s urban voter is not just ideological",
        body: [
          "The biggest mistake is to imagine the urban BJP voter as only a religious or ideological voter.",
          "That voter exists. But the BJP’s urban coalition is broader.",
          "In many cities, the BJP appeals to voters who see themselves as aspirational rather than traditionalist. They may care about infrastructure, roads, airports, metro systems, digital payments, urban cleanliness, national prestige, business confidence, or India’s global image. For these voters, the BJP is not merely a right-wing cultural party. It is also the party that claims to represent a stronger, more modern, more confident India.",
          "This is where India differs sharply from the Western urban pattern.",
          "In the American model, urban modernity often pushes voters away from the right. In India, urban modernity can coexist with nationalism, religion, market aspiration, and a demand for strong leadership.",
          "Urban India is not automatically progressive. It is aspirational first.",
        ],
      },
      {
        heading: "Cities reward visibility",
        body: [
          "Urban voters experience politics through visibility.",
          "They see highways, airports, metros, flyovers, redevelopment, digital governance, policing, municipal services, public events, and national branding. Whether or not these improvements are evenly distributed is a separate question. The point is that urban politics is highly visual.",
          "The BJP has been especially strong at converting visibility into political language. Infrastructure is not presented merely as public works. It is presented as proof of national transformation. A new airport, a cleaned-up riverfront, a metro line, or a large public event becomes part of a larger story: India is rising, and the BJP is managing that rise.",
          "This matters because urban voters are often more exposed to national media and national political messaging. They may vote in a local constituency, but they consume politics nationally. The BJP’s ability to presidentialise parliamentary elections has therefore mattered greatly in many urban seats.",
        ],
      },
      {
        heading: "Urban India is diverse, but diversity does not always mean liberalism",
        body: [
          "Another Western assumption is that diversity automatically produces progressive politics.",
          "India complicates that too.",
          "Indian cities are diverse, but they are also deeply segmented. People may live in the same city while belonging to different caste networks, language networks, religious communities, housing clusters, professional circles, and neighbourhood economies. Diversity does not automatically create a shared liberal identity.",
          "In fact, migration into cities can sometimes strengthen identity politics. A migrant community in Mumbai, Delhi, Surat, or Bengaluru may not abandon caste, religion, or region. It may reorganise those identities in a new urban setting.",
          "This is why urban India can be modern without being liberal in the Western sense. The city creates new ambitions, but it does not erase older identities. The BJP’s success lies partly in combining the two: modern aspiration and older civilisational identity.",
        ],
      },
      {
        heading: "The middle class matters",
        body: [
          "Urban India also has a large class of voters who think of politics through stability.",
          "This includes salaried workers, small business owners, traders, professionals, housing-society residents, and upwardly mobile families. Their concerns are not always ideological in a textbook sense. They may care about inflation, taxes, jobs, urban congestion, safety, corruption, or business confidence. But politically, they may still prefer a party that appears disciplined, centralised, and nationally dominant.",
          "The BJP’s appeal to this class is not accidental. It has built a language of governance that speaks to the middle-class desire for order and efficiency. The idea of a strong leader, a strong nation, and a strong state can be especially appealing in cities that feel chaotic.",
          "This does not mean all urban voters support the BJP. Cities like Chennai, Kolkata, Hyderabad, and parts of Kerala show that regional identity, linguistic politics, minority concentration, and strong state parties can limit or block BJP expansion. But where the BJP does succeed in cities, it is often because it has become the party of aspirational order.",
        ],
      },
      {
        heading: "Urban BJP strength is not uniform",
        body: [
          "The BJP’s urban story is powerful, but it is not universal.",
          "Coimbatore is not Bangalore South. Hyderabad is not Delhi. Mumbai South is not Varanasi. Kolkata Dakshin is not Gandhinagar. Each city has its own coalition structure.",
          "In Tamil Nadu, Dravidian politics limits the BJP’s urban conversion. In West Bengal, the TMC’s organisation and Bengali regional identity create a different urban battlefield. In Hyderabad, AIMIM’s local structure and religious geography make the seat unlike most BJP-versus-Congress contests. In Kerala, high literacy and urbanisation do not automatically produce BJP seats.",
          "So the real story is not “urban India votes BJP.”",
          "The real story is more interesting: urbanisation in India does not automatically produce anti-BJP politics.",
          "That is the flip.",
        ],
      },
      {
        heading: "What The 543 can test",
        body: [
          "This is where The 543 becomes useful.",
          "Instead of relying on vibes, we can ask constituency-level questions.",
          "Does the BJP perform better in more urban seats? Does it gain more in seats with higher mobile access, LPG access, or electricity coverage? Does the INC recover more strongly in seats with different development profiles? Are urban BJP seats safer, or just more visible? Where do regional parties block BJP despite urbanisation? Which cities behave like nationalised BJP seats, and which behave like regional-party strongholds?",
          "The early data in The 543 suggests that urbanisation and BJP performance are worth studying carefully. But this must be handled cautiously. A correlation between urban indicators and BJP swing is not proof that urbanisation causes BJP support. Urban seats also differ by state, candidate, alliance structure, caste composition, religion, media exposure, and local political history.",
          "The point is not to force a single answer.",
          "The point is to build a map of where the theory works — and where India breaks the theory.",
        ],
      },
      {
        heading: "The India exception",
        body: [
          "India’s cities are not conservative in the simple sense. They are not rural traditionalism transplanted into apartment buildings. They are aspirational, unequal, diverse, nationalised, and deeply political.",
          "That is why the BJP’s urban strength matters.",
          "It shows that the party’s success is not only built on rural Hindu mobilisation or welfare politics. It is also built on a powerful urban promise: that India can be modern without becoming Western-liberal, aspirational without becoming anti-nationalist, and economically forward-looking while still rooted in civilisational identity.",
          "That is the India exception.",
          "In many democracies, the city is where the right goes to lose.",
          "In India, the city is often where the BJP proves it can look like the future.",
        ],
      },
    ],
  },
];

export function getEssayBySlug(slug: string): Essay | undefined {
  return ESSAYS.find((essay) => essay.slug === slug);
}

export function getEssaysBySeries(series: string): Essay[] {
  return ESSAYS.filter((essay) => essay.series === series);
}
