/**
 * Central content store for the site.
 *
 * Editing the CV: update the arrays below — publications.html, teaching.html
 * and conferences.html all render straight from this file, so there is only
 * one place to keep in sync. Fields marked "[Add ...]" are placeholders the
 * site owner should fill in (links, abstracts, exact course codes, etc.).
 */

var SITE_DATA = {

  // ---------------------------------------------------------------------
  // Publications: rendered by publications.html
  // status drives the badge shown next to the year.
  // links: use "#" to keep an item on the page without an active link yet.
  // ---------------------------------------------------------------------
  publications: {

    published: [
      {
        title: "Locus of control and volunteering among older individuals in Europe",
        authors: "Almomani, M., & Onur, I.",
        venue: "Journal of Economic Studies",
        details: "53(9), 80–96",
        year: 2026,
        keywords: ["Ageing", "Volunteering", "Locus of control", "SHARE", "Europe"],
        abstract: "Examines how locus of control — the degree to which older individuals believe they can influence outcomes in their own lives — is associated with the probability and intensity of volunteering among older Europeans, using SHARE survey data.",
        links: { pdf: "#", doi: "#", replication: "#", slides: "" }
      },
      {
        title: "Governance of ageing and functional health: The impact of retirement policies on grip strength in Europe",
        authors: "Almomani, M., & Al-Masaeid, M.",
        venue: "International Journal of Health Governance",
        details: "31(1), 63–78",
        year: 2026,
        keywords: ["Retirement policy", "Functional health", "Grip strength", "SHARE", "Governance"],
        abstract: "Studies how variation in national retirement policy settings across Europe relates to a physical marker of functional health in older age, grip strength, drawing on harmonised SHARE data.",
        links: { pdf: "#", doi: "#", replication: "#", slides: "" }
      },
      {
        title: "Education as a safeguard: The influence of education on informal caregiving among retirees in Europe",
        authors: "Almomani, M., & Al-Masaeid, M.",
        venue: "The Journal of Adult Protection",
        details: "28(2), 63–75",
        year: 2026,
        keywords: ["Education", "Informal caregiving", "Retirement", "Ageing", "Europe"],
        abstract: "Investigates whether attained education level shapes the probability and burden of informal caregiving among retirees, with implications for adult protection and long-term care policy in Europe.",
        links: { pdf: "#", doi: "#", replication: "#", slides: "" }
      },
      {
        title: "Household size and domestic violence: Evidence from Jordan Population and Family Health Surveys (JPFHS)",
        authors: "Al-Masaeid, M., & Almomani, M.",
        venue: "Marriage & Family Review",
        details: "1–32",
        year: 2026,
        keywords: ["Household size", "Domestic violence", "Jordan", "JPFHS", "Development economics"],
        abstract: "Uses repeated cross-sections of the Jordan Population and Family Health Surveys to assess the relationship between household size and the incidence of domestic violence.",
        links: { pdf: "#", doi: "#", replication: "#", slides: "" }
      },
      {
        title: "More than just a home: The impact of household conditions on early childhood development in Jordan",
        authors: "Al-Masaeid, M., & Almomani, M.",
        venue: "Health Education",
        details: "1–18",
        year: 2026,
        keywords: ["Early childhood development", "Household conditions", "Jordan", "Human capital"],
        abstract: "Assesses how household living conditions relate to markers of early childhood development in Jordan, contributing to the human-capital and development-economics literature.",
        links: { pdf: "#", doi: "#", replication: "#", slides: "" }
      },
      {
        title: "The impact of education on instrumental activities of daily living: Evidence from Europe using SHARE data",
        authors: "Almomani, M., & Al-Masaeid, M.",
        venue: "Journal of Economic Studies",
        details: "52(9), 289–303",
        year: 2025,
        keywords: ["Education", "IADL", "Functional independence", "SHARE", "Ageing"],
        abstract: "Estimates the relationship between education and instrumental activities of daily living (IADL) among older Europeans, informing policy on education as a lever for healthy ageing.",
        links: { pdf: "#", doi: "#", replication: "#", slides: "" }
      },
      {
        title: "Do kids change the game? How parenthood reshapes intra-household decision-making: Evidence from Jordan",
        authors: "Al-Masaeid, M., & Almomani, M.",
        venue: "Applied Economics",
        details: "1–16",
        year: 2025,
        keywords: ["Intra-household bargaining", "Parenthood", "Jordan", "Applied economics"],
        abstract: "Examines how the transition to parenthood shifts intra-household decision-making dynamics, using household survey data from Jordan.",
        links: { pdf: "#", doi: "#", replication: "#", slides: "" }
      },
      {
        title: "Maternal education and early childhood development: Evidence from Jordan's Demographic and Health Survey",
        authors: "Al-Masaeid, M., & Almomani, M.",
        venue: "Health Education",
        details: "1–18",
        year: 2025,
        keywords: ["Maternal education", "Early childhood development", "Jordan", "DHS"],
        abstract: "Analyses the link between maternal education and early childhood development outcomes using Jordan's Demographic and Health Survey.",
        links: { pdf: "#", doi: "#", replication: "#", slides: "" }
      },
      {
        title: "Paying to tie the knot: Does education make marriage more expensive? Evidence from Jordan",
        authors: "Al-Masaeid, M., & Almomani, M.",
        venue: "Journal of Economic Studies",
        details: "52(9), 253–273",
        year: 2025,
        keywords: ["Marriage costs", "Education", "Jordan", "Household economics"],
        abstract: "Investigates whether higher education attainment is associated with higher marriage costs in Jordan, linking human-capital investment to household formation decisions.",
        links: { pdf: "#", doi: "#", replication: "#", slides: "" }
      }
    ],

    underReview: [
      {
        title: "Occupational variation in the impact of retirement on functional independence: Evidence from SHARE",
        authors: "Almomani, M., & Onur, I.",
        venue: "Journal of Health Economics",
        details: "Under review",
        year: 2026,
        keywords: ["Retirement", "Functional independence", "Occupation", "SHARE", "IV-2SLS"],
        abstract: "Uses an instrumental-variables strategy around statutory retirement ages to estimate how the effect of retirement on functional independence varies by occupational category across Europe.",
        links: { pdf: "#", doi: "", replication: "#", slides: "#" }
      },
      {
        title: "Emotional closeness and life expectancy: Cross-country evidence from Europe",
        authors: "Almomani, M.",
        venue: "Biodemography and Social Biology",
        details: "Under review",
        year: 2026,
        keywords: ["Emotional closeness", "Life expectancy", "Social ties", "Europe"],
        abstract: "Studies the association between reported emotional closeness to family and friends and subsequent life expectancy, using cross-country European survey data.",
        links: { pdf: "#", doi: "", replication: "#", slides: "#" }
      },
      {
        title: "Locus of control and functional independence in older adults: Evidence from Europe",
        authors: "Almomani, M.",
        venue: "International Journal of Social Economics",
        details: "Under review",
        year: 2026,
        keywords: ["Locus of control", "Functional independence", "Older adults", "Europe"],
        abstract: "Examines whether an internal locus of control is protective of functional independence in later life, using longitudinal European survey data.",
        links: { pdf: "#", doi: "", replication: "#", slides: "" }
      }
    ],

    workingPapers: [
      {
        title: "Can education reduce aged-care need? Evidence from Aboriginal and Torres Strait Islander adults in Australia",
        authors: "Almomani, M.",
        venue: "Working paper",
        details: "Draft available on request",
        year: 2026,
        keywords: ["Education", "Aged care", "Indigenous health", "Australia"],
        abstract: "Assesses whether education attainment reduces the likelihood of needing aged care among Aboriginal and Torres Strait Islander adults, with direct relevance to closing-the-gap policy design.",
        links: { pdf: "#", doi: "", replication: "", slides: "" }
      },
      {
        title: "Reducing preventable aged-care need: Retirement effects on functional independence among Aboriginal and Torres Strait Islander adults",
        authors: "Almomani, M.",
        venue: "Working paper",
        details: "Draft available on request",
        year: 2026,
        keywords: ["Retirement", "Aged care", "Functional independence", "Indigenous health"],
        abstract: "Investigates how retirement timing relates to functional independence among Aboriginal and Torres Strait Islander adults, informing preventive aged-care policy.",
        links: { pdf: "#", doi: "", replication: "", slides: "" }
      },
      {
        title: "Hope as a modifiable determinant of healthy ageing: Evidence for preventive obesity policy in older Australians using HILDA",
        authors: "Almomani, M.",
        venue: "Working paper",
        details: "Draft available on request",
        year: 2025,
        keywords: ["Hope", "Healthy ageing", "Obesity policy", "HILDA"],
        abstract: "Explores psychological hope as a modifiable determinant of healthy ageing and weight outcomes among older Australians, using the HILDA Survey.",
        links: { pdf: "#", doi: "", replication: "", slides: "" }
      },
      {
        title: "Costs of age-related care needs among Australian women: Evidence from the Australian Longitudinal Study on Women's Health",
        authors: "Almomani, M.",
        venue: "Working paper",
        details: "Draft available on request",
        year: 2025,
        keywords: ["Aged care costs", "Women's health", "ALSWH", "Ageing"],
        abstract: "Quantifies the costs associated with age-related care needs among Australian women using the Australian Longitudinal Study on Women's Health (ALSWH).",
        links: { pdf: "#", doi: "", replication: "", slides: "" }
      },
      {
        title: "Functional decline, aged-care use and wellbeing among older adults in South Australia: Evidence from the HILDA Survey",
        authors: "Almomani, M.",
        venue: "Working paper",
        details: "Draft available on request",
        year: 2025,
        keywords: ["Functional decline", "Aged care", "Wellbeing", "HILDA", "South Australia"],
        abstract: "Examines the relationship between functional decline, aged-care service use and subjective wellbeing among older South Australians, using the HILDA Survey.",
        links: { pdf: "#", doi: "", replication: "", slides: "" }
      }
    ],

    conferencePapers: [
      {
        title: "Occupational variation in the impact of retirement on functional independence: Evidence from SHARE",
        authors: "Almomani, M., & Onur, I.",
        venue: "Netspar International Pension Workshop",
        details: "Presenter and session chair — Leiden, the Netherlands",
        year: 2026,
        keywords: ["Retirement", "Pensions", "SHARE", "Functional independence"],
        abstract: "Conference presentation of the retirement and functional-independence study, delivered as presenter and session chair at the Netspar International Pension Workshop.",
        links: { pdf: "", doi: "", replication: "", slides: "#" }
      },
      {
        title: "Education and volunteering for older adults: Cross-country evidence from Europe",
        authors: "Almomani, M., & Onur, I.",
        venue: "Gateway to Global Aging Data Conference, Boston University",
        details: "Presenter — Boston, USA",
        year: 2025,
        keywords: ["Education", "Volunteering", "Ageing", "SHARE"],
        abstract: "Presented findings on education and volunteering behaviour among older Europeans at the Gateway to Global Aging Data Conference.",
        links: { pdf: "", doi: "", replication: "", slides: "#" }
      },
      {
        title: "Emotional closeness and life expectancy: Cross-country evidence from Europe",
        authors: "Almomani, M.",
        venue: "SHARE-Gateway User Conference",
        details: "Presenter — Berlin, Germany",
        year: 2024,
        keywords: ["Emotional closeness", "Life expectancy", "SHARE"],
        abstract: "Presented cross-country evidence on emotional closeness and life expectancy at the SHARE-Gateway User Conference in Berlin.",
        links: { pdf: "", doi: "", replication: "", slides: "#" }
      }
    ],

    workInProgress: [
      {
        title: "[Add working title]",
        authors: "Almomani, M., & [Add co-author]",
        venue: "Work in progress",
        details: "[Add expected outlet or milestone]",
        year: new Date().getFullYear(),
        keywords: ["[Add keywords]"],
        abstract: "This is a placeholder slot for a project that is still in progress. Replace this text with a short project description once the paper has a stable title and abstract.",
        links: { pdf: "", doi: "", replication: "", slides: "" }
      }
    ]
  },

  // ---------------------------------------------------------------------
  // Teaching: rendered by teaching.html
  // ---------------------------------------------------------------------
  teaching: [
    {
      course: "Innovation Academy in Digital Business — Agile, DevOps & Design Thinking",
      institution: "Adelaide University, in partnership with Accenture",
      level: "Professional / postgraduate short-course",
      years: "2025 – present",
      description: "Academic lead for course design and delivery of Agile, DevOps and Design Thinking training under the Accenture–Adelaide University partnership, including leading course redevelopment. [Add specific unit/course codes.]"
    },
    {
      course: "Economics, econometrics, statistics and applied research methods",
      institution: "College of Business, Government and Law, Flinders University",
      level: "Undergraduate and postgraduate",
      years: "2024 – present",
      description: "Teaching academic covering economics, applied econometrics, statistics, data analysis and applied research methods for business and economics students. [Add specific unit/course codes.]"
    },
    {
      course: "Undergraduate economics — coding, data analysis and digital business methods",
      institution: "Flinders University / Adelaide University",
      level: "Undergraduate",
      years: "2024 – present",
      description: "Supports coursework connecting economic reasoning with coding for business, digital business practice and data analysis, complementing core econometrics teaching. [Add specific unit/course codes.]"
    },
    {
      course: "Undergraduate economics (teaching assistant)",
      institution: "Yarmouk University, Jordan",
      level: "Undergraduate",
      years: "2016 – 2019",
      description: "Taught tutorials and supported course delivery in introductory and intermediate economics while completing the B.S. and M.A. in Economics."
    }
  ],

  // ---------------------------------------------------------------------
  // Map pins: rendered by conferences.html (Leaflet)
  // category one of: "academic" | "conference" | "industry" | "dataset"
  // Each location can list several "activities" so one city can carry
  // multiple pieces of history (e.g. Adelaide = PhD + two appointments).
  //
  // TO ADD A NEW PIN: copy an object below, update lat/lng (decimal
  // degrees), category, and the activities array, then save — the map
  // and the accessible table underneath it both read from this array.
  // ---------------------------------------------------------------------
  locations: [
    {
      id: "adelaide",
      city: "Adelaide",
      country: "Australia",
      lat: -34.9285,
      lng: 138.6007,
      category: "academic",
      activities: [
        {
          year: "2025 – present",
          org: "Adelaide University",
          role: "Teaching Academic",
          topic: "Lead, Innovation Academy in Digital Business — Agile, DevOps and Design Thinking (Accenture partnership)"
        },
        {
          year: "2024 – present",
          org: "Flinders University, College of Business, Government and Law",
          role: "Teaching Academic",
          topic: "PhD in Economics (2025); teaching in economics, econometrics and applied research methods"
        }
      ]
    },
    {
      id: "leiden",
      city: "Leiden",
      country: "Netherlands",
      lat: 52.1601,
      lng: 4.4970,
      category: "conference",
      activities: [
        {
          year: "2026",
          org: "Netspar International Pension Workshop",
          role: "Presenter & session chair",
          topic: "Occupational variation in the impact of retirement on functional independence: evidence from SHARE"
        }
      ]
    },
    {
      id: "boston",
      city: "Boston",
      country: "United States",
      lat: 42.3601,
      lng: -71.0589,
      category: "conference",
      activities: [
        {
          year: "2025",
          org: "Gateway to Global Aging Data Conference, Boston University",
          role: "Presenter",
          topic: "Education and volunteering for older adults: cross-country evidence from Europe"
        }
      ]
    },
    {
      id: "berlin",
      city: "Berlin",
      country: "Germany",
      lat: 52.5200,
      lng: 13.4050,
      category: "conference",
      activities: [
        {
          year: "2024",
          org: "SHARE-Gateway User Conference",
          role: "Presenter",
          topic: "Emotional closeness and life expectancy: cross-country evidence from Europe"
        }
      ]
    },
    {
      id: "doha",
      city: "Doha",
      country: "Qatar",
      lat: 25.2854,
      lng: 51.5310,
      category: "industry",
      activities: [
        {
          year: "2019 – 2022",
          org: "Mubadala",
          role: "Economic and Energy Market Analyst",
          topic: "Commercial economic and energy-market analysis for business decision-making"
        }
      ]
    },
    {
      id: "irbid",
      city: "Irbid",
      country: "Jordan",
      lat: 32.5556,
      lng: 35.8500,
      category: "academic",
      activities: [
        {
          year: "2016 – 2019",
          org: "Yarmouk University",
          role: "Teaching Assistant",
          topic: "Undergraduate economics teaching; B.S. (2015) and M.A. (2019) in Economics"
        }
      ]
    },
    {
      id: "dataset-europe",
      city: "Frankfurt (SHARE coordination)",
      country: "Pan-European",
      lat: 50.1109,
      lng: 8.6821,
      category: "dataset",
      activities: [
        {
          year: "Ongoing",
          org: "SHARE — Survey of Health, Ageing and Retirement in Europe",
          role: "Data source",
          topic: "Cross-national longitudinal survey spanning 27+ European countries; primary data source for the ageing, retirement and health research stream"
        }
      ]
    },
    {
      id: "dataset-australia",
      city: "Canberra (national survey coverage)",
      country: "Australia",
      lat: -35.2809,
      lng: 149.1300,
      category: "dataset",
      activities: [
        {
          year: "Ongoing",
          org: "HILDA Survey & ALSWH",
          role: "Data source",
          topic: "Household, Income and Labour Dynamics in Australia (HILDA) and the Australian Longitudinal Study on Women's Health (ALSWH), used across the Australian ageing and aged-care research stream"
        }
      ]
    },
    {
      id: "dataset-jordan",
      city: "Amman (JLMPS coverage)",
      country: "Jordan",
      lat: 31.9454,
      lng: 35.9284,
      category: "dataset",
      activities: [
        {
          year: "Ongoing",
          org: "Jordan Labor Market Panel Survey (JLMPS) & Jordan DHS/JPFHS",
          role: "Data source",
          topic: "Labour-market, household and demographic-health panel data underpinning the Jordan development-economics research stream"
        }
      ]
    }
  ]
};
