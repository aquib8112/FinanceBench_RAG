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

function groupByCompany(data) {
    const result = {};

    for (const key in data) {
        const item = data[key];
        const company = item.company;

        if (!result[company]) result[company] = {};
        if (!result[company][item.year]) result[company][item.year] = [];

        result[company][item.year].push(item);
    }

    return result;
}

function renderFilings() {
    const container = document.getElementById("filings-container");
    const grouped = groupByCompany(documentsMap);

    Object.keys(grouped).sort().forEach(company => {
        const companyBlock = document.createElement("div");
        companyBlock.className = "company-block";

        const title = document.createElement("div");
        title.className = "company-title";
        title.textContent = company.toUpperCase();
        companyBlock.appendChild(title);

        const years = grouped[company];
        Object.keys(years).sort((a,b) => b - a).forEach(year => {
            years[year].forEach(filing => {
                const div = document.createElement("div");
                div.className = "filing";

                const quarter = filing.quarter ? ` Q${filing.quarter}` : "";
                div.innerHTML = `
                    <span class="year">${year}</span>
                    <span class="type">(${filing.document_type.toUpperCase()}${quarter})</span>
                    - ${filing.document_name}
                `;

                companyBlock.appendChild(div);
            });
        });

        container.appendChild(companyBlock);
    });
}

renderFilings();
