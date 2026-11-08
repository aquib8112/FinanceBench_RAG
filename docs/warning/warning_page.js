const documentsMap = {
    "3M_2018_10K": { document_name: "3M_2018_10K", company: "3m", year: 2018, document_type: "10k", quarter: null, date: null },
    "3M_2022_10K": { document_name: "3M_2022_10K", company: "3m", year: 2022, document_type: "10k", quarter: null, date: null },
    "3M_2023Q2_10Q": { document_name: "3M_2023Q2_10Q", company: "3m", year: 2023, document_type: "10q", quarter: "2", date: null },
    "ACTIVISIONBLIZZARD_2019_10K": { document_name: "ACTIVISIONBLIZZARD_2019_10K", company: "activisionblizzard", year: 2019, document_type: "10k", quarter: null, date: null },
    "ADOBE_2015_10K": { document_name: "ADOBE_2015_10K", company: "adobe", year: 2015, document_type: "10k", quarter: null, date: null },
    "ADOBE_2016_10K": { document_name: "ADOBE_2016_10K", company: "adobe", year: 2016, document_type: "10k", quarter: null, date: null },
    "ADOBE_2017_10K": { document_name: "ADOBE_2017_10K", company: "adobe", year: 2017, document_type: "10k", quarter: null, date: null },
    "ADOBE_2022_10K": { document_name: "ADOBE_2022_10K", company: "adobe", year: 2022, document_type: "10k", quarter: null, date: null },
    "AES_2022_10K": { document_name: "AES_2022_10K", company: "aes", year: 2022, document_type: "10k", quarter: null, date: null },
    "AMAZON_2017_10K": { document_name: "AMAZON_2017_10K", company: "amazon", year: 2017, document_type: "10k", quarter: null, date: null },
    "AMAZON_2019_10K": { document_name: "AMAZON_2019_10K", company: "amazon", year: 2019, document_type: "10k", quarter: null, date: null },
    "AMCOR_2020_10K": { document_name: "AMCOR_2020_10K", company: "amcor", year: 2020, document_type: "10k", quarter: null, date: null },
    "AMCOR_2022_8K_dated-2022-07-01": { document_name: "AMCOR_2022_8K_dated-2022-07-01", company: "amcor", year: 2022, document_type: "8k", quarter: "Q3", date: "2022-07-01" },
    "AMCOR_2023Q2_10Q": { document_name: "AMCOR_2023Q2_10Q", company: "amcor", year: 2023, document_type: "10q", quarter: "2", date: null },
    "AMCOR_2023Q4_EARNINGS": { document_name: "AMCOR_2023Q4_EARNINGS", company: "amcor", year: 2023, document_type: "earnings", quarter: "4", date: null },
    "AMCOR_2023_10K": { document_name: "AMCOR_2023_10K", company: "amcor", year: 2023, document_type: "10k", quarter: null, date: null },
    "AMD_2015_10K": { document_name: "AMD_2015_10K", company: "amd", year: 2015, document_type: "10k", quarter: null, date: null },
    "AMD_2022_10K": { document_name: "AMD_2022_10K", company: "amd", year: 2022, document_type: "10k", quarter: null, date: null },
    "AMERICANEXPRESS_2022_10K": { document_name: "AMERICANEXPRESS_2022_10K", company: "americanexpress", year: 2022, document_type: "10k", quarter: null, date: null },
    "AMERICANWATERWORKS_2020_10K": { document_name: "AMERICANWATERWORKS_2020_10K", company: "americanwaterworks", year: 2020, document_type: "10k", quarter: null, date: null },
    "AMERICANWATERWORKS_2021_10K": { document_name: "AMERICANWATERWORKS_2021_10K", company: "americanwaterworks", year: 2021, document_type: "10k", quarter: null, date: null },
    "AMERICANWATERWORKS_2022_10K": { document_name: "AMERICANWATERWORKS_2022_10K", company: "americanwaterworks", year: 2022, document_type: "10k", quarter: null, date: null },
    "BESTBUY_2017_10K": { document_name: "BESTBUY_2017_10K", company: "bestbuy", year: 2017, document_type: "10k", quarter: null, date: null },
    "BESTBUY_2019_10K": { document_name: "BESTBUY_2019_10K", company: "bestbuy", year: 2019, document_type: "10k", quarter: null, date: null },
    "BESTBUY_2023_10K": { document_name: "BESTBUY_2023_10K", company: "bestbuy", year: 2023, document_type: "10k", quarter: null, date: null },
    "BESTBUY_2024Q2_10Q": { document_name: "BESTBUY_2024Q2_10Q", company: "bestbuy", year: 2024, document_type: "10q", quarter: "2", date: null },
    "BLOCK_2016_10K": { document_name: "BLOCK_2016_10K", company: "block", year: 2016, document_type: "10k", quarter: null, date: null },
    "BLOCK_2020_10K": { document_name: "BLOCK_2020_10K", company: "block", year: 2020, document_type: "10k", quarter: null, date: null },
    "BOEING_2018_10K": { document_name: "BOEING_2018_10K", company: "boeing", year: 2018, document_type: "10k", quarter: null, date: null },
    "BOEING_2022_10K": { document_name: "BOEING_2022_10K", company: "boeing", year: 2022, document_type: "10k", quarter: null, date: null },
    "COCACOLA_2017_10K": { document_name: "COCACOLA_2017_10K", company: "cocacola", year: 2017, document_type: "10k", quarter: null, date: null },
    "COCACOLA_2021_10K": { document_name: "COCACOLA_2021_10K", company: "cocacola", year: 2021, document_type: "10k", quarter: null, date: null },
    "COCACOLA_2022_10K": { document_name: "COCACOLA_2022_10K", company: "cocacola", year: 2022, document_type: "10k", quarter: null, date: null },
    "CORNING_2020_10K": { document_name: "CORNING_2020_10K", company: "corning", year: 2020, document_type: "10k", quarter: null, date: null },
    "CORNING_2021_10K": { document_name: "CORNING_2021_10K", company: "corning", year: 2021, document_type: "10k", quarter: null, date: null },
    "CORNING_2022_10K": { document_name: "CORNING_2022_10K", company: "corning", year: 2022, document_type: "10k", quarter: null, date: null },
    "COSTCO_2021_10K": { document_name: "COSTCO_2021_10K", company: "costco", year: 2021, document_type: "10k", quarter: null, date: null },
    "CVSHEALTH_2018_10K": { document_name: "CVSHEALTH_2018_10K", company: "cvshealth", year: 2018, document_type: "10k", quarter: null, date: null },
    "CVSHEALTH_2022_10K": { document_name: "CVSHEALTH_2022_10K", company: "cvshealth", year: 2022, document_type: "10k", quarter: null, date: null },
    "FOOTLOCKER_2022_8K_dated-2022-05-20": { document_name: "FOOTLOCKER_2022_8K_dated-2022-05-20", company: "footlocker", year: 2022, document_type: "8k", quarter: "Q2", date: "2022-05-20" },
    "FOOTLOCKER_2022_8K_dated_2022-08-19": { document_name: "FOOTLOCKER_2022_8K_dated_2022-08-19", company: "footlocker", year: 2022, document_type: "8k", quarter: "Q3", date: "2022-08-19" },
    "GENERALMILLS_2019_10K": { document_name: "GENERALMILLS_2019_10K", company: "generalmills", year: 2019, document_type: "10k", quarter: null, date: null },
    "GENERALMILLS_2020_10K": { document_name: "GENERALMILLS_2020_10K", company: "generalmills", year: 2020, document_type: "10k", quarter: null, date: null },
    "GENERALMILLS_2022_10K": { document_name: "GENERALMILLS_2022_10K", company: "generalmills", year: 2022, document_type: "10k", quarter: null, date: null },
    "JOHNSON_JOHNSON_2022Q4_EARNINGS": { document_name: "JOHNSON_JOHNSON_2022Q4_EARNINGS", company: "johnson_johnson", year: 2022, document_type: "earnings", quarter: "4", date: null },
    "JOHNSON_JOHNSON_2022_10K": { document_name: "JOHNSON_JOHNSON_2022_10K", company: "johnson_johnson", year: 2022, document_type: "10k", quarter: null, date: null },
    "JOHNSON_JOHNSON_2023Q2_EARNINGS": { document_name: "JOHNSON_JOHNSON_2023Q2_EARNINGS", company: "johnson_johnson", year: 2023, document_type: "earnings", quarter: "2", date: null },
    "JOHNSON_JOHNSON_2023_8K_dated-2023-08-30": { document_name: "JOHNSON_JOHNSON_2023_8K_dated-2023-08-30", company: "johnson_johnson", year: 2023, document_type: "8k", quarter: "Q3", date: "2023-08-30" },
    "JPMORGAN_2021Q1_10Q": { document_name: "JPMORGAN_2021Q1_10Q", company: "jpmorgan", year: 2021, document_type: "10q", quarter: "1", date: null },
    "JPMORGAN_2022Q2_10Q": { document_name: "JPMORGAN_2022Q2_10Q", company: "jpmorgan", year: 2022, document_type: "10q", quarter: "2", date: null },
    "JPMORGAN_2022_10K": { document_name: "JPMORGAN_2022_10K", company: "jpmorgan", year: 2022, document_type: "10k", quarter: null, date: null },
    "JPMORGAN_2023Q2_10Q": { document_name: "JPMORGAN_2023Q2_10Q", company: "jpmorgan", year: 2023, document_type: "10q", quarter: "2", date: null },
    "KRAFTHEINZ_2019_10K": { document_name: "KRAFTHEINZ_2019_10K", company: "kraftheinz", year: 2019, document_type: "10k", quarter: null, date: null },
    "LOCKHEEDMARTIN_2020_10K": { document_name: "LOCKHEEDMARTIN_2020_10K", company: "lockheedmartin", year: 2020, document_type: "10k", quarter: null, date: null },
    "LOCKHEEDMARTIN_2021_10K": { document_name: "LOCKHEEDMARTIN_2021_10K", company: "lockheedmartin", year: 2021, document_type: "10k", quarter: null, date: null },
    "LOCKHEEDMARTIN_2022_10K": { document_name: "LOCKHEEDMARTIN_2022_10K", company: "lockheedmartin", year: 2022, document_type: "10k", quarter: null, date: null },
    "MGMRESORTS_2018_10K": { document_name: "MGMRESORTS_2018_10K", company: "mgmresorts", year: 2018, document_type: "10k", quarter: null, date: null },
    "MGMRESORTS_2020_10K": { document_name: "MGMRESORTS_2020_10K", company: "mgmresorts", year: 2020, document_type: "10k", quarter: null, date: null },
    "MGMRESORTS_2022Q4_EARNINGS": { document_name: "MGMRESORTS_2022Q4_EARNINGS", company: "mgmresorts", year: 2022, document_type: "earnings", quarter: "4", date: null },
    "MGMRESORTS_2022_10K": { document_name: "MGMRESORTS_2022_10K", company: "mgmresorts", year: 2022, document_type: "10k", quarter: null, date: null },
    "MGMRESORTS_2023Q2_10Q": { document_name: "MGMRESORTS_2023Q2_10Q", company: "mgmresorts", year: 2023, document_type: "10q", quarter: "2", date: null },
    "MICROSOFT_2016_10K": { document_name: "MICROSOFT_2016_10K", company: "microsoft", year: 2016, document_type: "10k", quarter: null, date: null },
    "MICROSOFT_2023_10K": { document_name: "MICROSOFT_2023_10K", company: "microsoft", year: 2023, document_type: "10k", quarter: null, date: null },
    "NETFLIX_2015_10K": { document_name: "NETFLIX_2015_10K", company: "netflix", year: 2015, document_type: "10k", quarter: null, date: null },
    "NETFLIX_2017_10K": { document_name: "NETFLIX_2017_10K", company: "netflix", year: 2017, document_type: "10k", quarter: null, date: null },
    "NIKE_2018_10K": { document_name: "NIKE_2018_10K", company: "nike", year: 2018, document_type: "10k", quarter: null, date: null },
    "NIKE_2019_10K": { document_name: "NIKE_2019_10K", company: "nike", year: 2019, document_type: "10k", quarter: null, date: null },
    "NIKE_2021_10K": { document_name: "NIKE_2021_10K", company: "nike", year: 2021, document_type: "10k", quarter: null, date: null },
    "NIKE_2023_10K": { document_name: "NIKE_2023_10K", company: "nike", year: 2023, document_type: "10k", quarter: null, date: null },
    "PAYPAL_2022_10K": { document_name: "PAYPAL_2022_10K", company: "paypal", year: 2022, document_type: "10k", quarter: null, date: null },
    "PEPSICO_2021_10K": { document_name: "PEPSICO_2021_10K", company: "pepsico", year: 2021, document_type: "10k", quarter: null, date: null },
    "PEPSICO_2022_10K": { document_name: "PEPSICO_2022_10K", company: "pepsico", year: 2022, document_type: "10k", quarter: null, date: null },
    "PEPSICO_2023Q1_EARNINGS": { document_name: "PEPSICO_2023Q1_EARNINGS", company: "pepsico", year: 2023, document_type: "earnings", quarter: "1", date: null },
    "PEPSICO_2023_8K_dated-2023-05-05": { document_name: "PEPSICO_2023_8K_dated-2023-05-05", company: "pepsico", year: 2023, document_type: "8k", quarter: "Q2", date: "2023-05-05" },
    "PEPSICO_2023_8K_dated-2023-05-30": { document_name: "PEPSICO_2023_8K_dated-2023-05-30", company: "pepsico", year: 2023, document_type: "8k", quarter: "Q2", date: "2023-05-30" },
    "PFIZER_2021_10K": { document_name: "PFIZER_2021_10K", company: "pfizer", year: 2021, document_type: "10k", quarter: null, date: null },
    "Pfizer_2023Q2_10Q": { document_name: "Pfizer_2023Q2_10Q", company: "pfizer", year: 2023, document_type: "10q", quarter: "2", date: null },
    "ULTABEAUTY_2023Q4_EARNINGS": { document_name: "ULTABEAUTY_2023Q4_EARNINGS", company: "ultabeauty", year: 2023, document_type: "earnings", quarter: "4", date: null },
    "ULTABEAUTY_2023_10K": { document_name: "ULTABEAUTY_2023_10K", company: "ultabeauty", year: 2023, document_type: "10k", quarter: null, date: null },
    "VERIZON_2021_10K": { document_name: "VERIZON_2021_10K", company: "verizon", year: 2021, document_type: "10k", quarter: null, date: null },
    "VERIZON_2022_10K": { document_name: "VERIZON_2022_10K", company: "verizon", year: 2022, document_type: "10k", quarter: null, date: null },
    "WALMART_2018_10K": { document_name: "WALMART_2018_10K", company: "walmart", year: 2018, document_type: "10k", quarter: null, date: null },
    "WALMART_2019_10K": { document_name: "WALMART_2019_10K", company: "walmart", year: 2019, document_type: "10k", quarter: null, date: null },
    "WALMART_2020_10K": { document_name: "WALMART_2020_10K", company: "walmart", year: 2020, document_type: "10k", quarter: null, date: null },
}


const companyNames = {
  "3m": "3M", aes: "AES", amd: "AMD", activisionblizzard: "Activision Blizzard",
  americanexpress: "American Express", americanwaterworks: "American Water Works",
  bestbuy: "Best Buy", cocacola: "Coca-Cola", cvshealth: "CVS Health",
  footlocker: "Foot Locker", generalmills: "General Mills", johnson_johnson: "Johnson & Johnson",
  jpmorgan: "JPMorgan", kraftheinz: "Kraft Heinz", lockheedmartin: "Lockheed Martin",
  mgmresorts: "MGM Resorts", paypal: "PayPal", pepsico: "PepsiCo", ultabeauty: "Ulta Beauty"
};
const filingTypes = { "10k": "10-K", "10q": "10-Q", "8k": "8-K", earnings: "Earnings" };
const companyName = filing => companyNames[filing.company] || filing.company[0].toUpperCase() + filing.company.slice(1);
const quarter = filing => filing.quarter ? String(filing.quarter).replace(/^q/i, "") : "";
const normalize = value => value.toLowerCase().replace(/[\s&._-]/g, "");
const dateFormat = new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric", year: "numeric", timeZone: "UTC" });
const filings = Object.values(documentsMap).sort((a, b) =>
  companyName(a).localeCompare(companyName(b), "en", { sensitivity: "base" }) ||
  b.year - a.year || Number(quarter(b) || 4) - Number(quarter(a) || 4) ||
  (b.date || "").localeCompare(a.date || "") || a.document_type.localeCompare(b.document_type)
);
const search = document.querySelector("#company-search");
const tbody = document.querySelector("#filings-body");

function renderFilings() {
  const query = normalize(search.value.trim());
  const visible = filings.filter(filing => normalize(companyName(filing)).includes(query));
  const fragment = document.createDocumentFragment();
  visible.forEach(filing => {
    const row = document.createElement("tr");
    row.innerHTML = '<th scope="row"></th><td><span class="period"></span></td><td><span class="filing-badge"></span></td>';
    row.querySelector("th").textContent = companyName(filing);
    row.querySelector(".period").textContent = filing.year + (quarter(filing) ? " Q" + quarter(filing) : "");
    row.querySelector(".filing-badge").textContent = filingTypes[filing.document_type];
    if (filing.date) {
      const date = document.createElement("time");
      date.className = "report-date";
      date.dateTime = filing.date;
      date.textContent = dateFormat.format(new Date(filing.date + "T00:00:00Z"));
      row.querySelector("td").append(date);
    }
    fragment.append(row);
  });
  tbody.replaceChildren(fragment);
  const count = new Set(visible.map(filing => filing.company)).size;
  document.querySelector("#results-count").textContent =
    (query ? visible.length + " of " : "") + filings.length + " filings \u00b7 " +
    count + (count === 1 ? " company" : " companies");
  document.querySelector(".empty-state").hidden = visible.length > 0;
}

search.addEventListener("input", renderFilings);
renderFilings();
