import fs from 'fs'
import path from 'path'

const outputDir = 'C:/Projects/velvet-elves-data'

const pageWidth = 612
const pageHeight = 792
const marginX = 50
const topY = 744
const bottomY = 54
const maxWidth = pageWidth - marginX * 2

const title = 'REAL ESTATE PURCHASE AGREEMENT'
const subtitle = 'AI Wizard Transaction Batch Fixture - Not For Real Transaction Use'

const transactions = [
  {
    acceptDate: '2026-06-19',
    id: 'TX-20260619-CEDAR',
    seller: {
      names: 'Rowan Vega and Celeste Vega',
      status: 'Married',
      address: '7712 Orchard Knoll Drive, Cuyahoga Falls, OH 44223',
      homePhone: '330-555-6101',
      workPhone: '330-555-6102',
      email: 'rowan.vega@minafter.com; celeste.vega@minafter.com',
    },
    buyer: {
      names: 'Harper Kim and Nolan Kim',
      status: 'Married',
      address: '1440 Ridgeview Avenue, Akron, OH 44313',
      homePhone: '330-555-7101',
      workPhone: '330-555-7102',
      email: 'harper.kim@minafter.com; nolan.kim@minafter.com',
    },
    property: {
      address: '2148 Cedar Mill Road',
      cityStateZip: 'Akron, OH 44312',
      county: 'Summit',
      parcel: '67-21901-002',
      included: 'Kitchen appliances, washer, dryer, window blinds, patio furniture',
      excluded: "Seller's wall-mounted television, garage shelving, outdoor grill",
      leadPaint: 'No lead-based paint disclosure required because the home was built in 1986',
    },
    price: 418750,
    earnest: 8500,
    downPayment: 41875,
    loanAmount: 376875,
    financingType: 'Conventional mortgage',
    occupancy: 'Buyer intends to occupy the property as a primary residence',
    closingDays: 42,
    title: {
      company: 'Anchor Title Services',
      contact: 'Marin Holt',
      email: 'marin.holt@minafter.com',
      phone: '330-555-8101',
      closingMode: 'Title / escrow closing',
      orderedBy: 'Seller',
    },
    warranty: {
      status: 'Included',
      orderedBy: 'Seller',
      provider: 'BrightHouse Home Warranty',
      email: 'brighthouse.support@minafter.com',
    },
    hoa: {
      name: 'Glen Hollow Homeowners Association',
      delivery: 'Seller shall deliver HOA documents within seven (7) days of acceptance',
    },
    contacts: {
      listingAgent: 'Gia Bennett, Summit Porch Realty, gia.bennett@minafter.com, 330-555-1201',
      buyersAgent: 'Omar Reed, MetroStone Realty, omar.reed@minafter.com, 330-555-2201',
      loanOfficer: 'Lena Park, First River Lending, lena.park@minafter.com, 330-555-3201',
      attorney: 'Quinn Shaw, Shaw Legal Group, quinn.shaw@minafter.com, 330-555-4201',
      inspector: 'Theo Burns, Northline Inspections, theo.burns@minafter.com, 330-555-5201',
      appraiser: 'Iris Lane, Summit Appraisal Partners, iris.lane@minafter.com, 330-555-6201',
    },
  },
  {
    acceptDate: '2026-06-22',
    id: 'TX-20260622-HARBOR',
    seller: {
      names: 'Miles Stone and Aisha Stone',
      status: 'Married',
      address: '441 West Juniper Lane, Lakewood, OH 44107',
      homePhone: '216-555-6103',
      workPhone: '216-555-6104',
      email: 'miles.stone@minafter.com; aisha.stone@minafter.com',
    },
    buyer: {
      names: 'Claire Nguyen',
      status: 'Single',
      address: '88 West 9th Street Apt 12B, Cleveland, OH 44113',
      homePhone: '216-555-7103',
      workPhone: '216-555-7104',
      email: 'claire.nguyen@minafter.com',
    },
    property: {
      address: '3380 Harborview Court',
      cityStateZip: 'Cleveland, OH 44113',
      county: 'Cuyahoga',
      parcel: '14-802-033',
      included: 'Stainless appliances, window treatments, smart thermostat, storage locker 4',
      excluded: "Seller's bicycle rack, balcony planters, portable kitchen island",
      leadPaint: 'Disclosure required because the home was built before 1978',
    },
    price: 526000,
    earnest: 12000,
    downPayment: 18410,
    loanAmount: 507590,
    financingType: 'FHA mortgage',
    occupancy: 'Buyer intends to occupy the property as a primary residence',
    closingDays: 45,
    title: {
      company: 'Lakefront Title Agency',
      contact: 'Soren Hill',
      email: 'soren.hill@minafter.com',
      phone: '216-555-8103',
      closingMode: 'Split closing with remote notarization',
      orderedBy: 'Buyer',
    },
    warranty: {
      status: 'Included',
      orderedBy: 'Buyer',
      provider: 'EverSure Home Warranty',
      email: 'eversure.claims@minafter.com',
    },
    hoa: {
      name: 'Harborview Condominium Association',
      delivery: 'Seller shall deliver resale certificate and condominium documents within five (5) days of acceptance',
    },
    contacts: {
      listingAgent: 'Paige Monroe, Lake City Realty, paige.monroe@minafter.com, 216-555-1203',
      buyersAgent: 'Andre Miles, Civic Key Realty, andre.miles@minafter.com, 216-555-2203',
      loanOfficer: 'Bianca Flores, Harbor Home Loans, bianca.flores@minafter.com, 216-555-3203',
      attorney: 'Reese Kaplan, Kaplan Closing Counsel, reese.kaplan@minafter.com, 216-555-4203',
      inspector: 'Jonas Bell, Urban Home Inspectors, jonas.bell@minafter.com, 216-555-5203',
      appraiser: 'Sasha Voss, Lakefront Valuation, sasha.voss@minafter.com, 216-555-6203',
    },
  },
  {
    acceptDate: '2026-06-25',
    id: 'TX-20260625-WILLOW',
    seller: {
      names: 'Bennett Ortiz',
      status: 'Single',
      address: '5099 Hyland Drive, Grove City, OH 43123',
      homePhone: '614-555-6105',
      workPhone: '614-555-6106',
      email: 'bennett.ortiz@minafter.com',
    },
    buyer: {
      names: 'Morgan Price and Samira Price',
      status: 'Married',
      address: '3194 Broadstone Court, Columbus, OH 43221',
      homePhone: '614-555-7105',
      workPhone: '614-555-7106',
      email: 'morgan.price@minafter.com; samira.price@minafter.com',
    },
    property: {
      address: '742 Willowbend Lane',
      cityStateZip: 'Grove City, OH 43123',
      county: 'Franklin',
      parcel: '040-017945-00',
      included: 'Range, refrigerator, dishwasher, microwave, garage opener remotes',
      excluded: "Seller's freezer, nursery curtains, portable basketball hoop",
      leadPaint: 'No lead-based paint disclosure required because the home was built in 1998',
    },
    price: 299900,
    earnest: 5000,
    downPayment: 0,
    loanAmount: 299900,
    financingType: 'VA mortgage',
    occupancy: 'Buyer intends to occupy the property as a primary residence',
    closingDays: 43,
    title: {
      company: 'Buckeye Land Title',
      contact: 'Drew Linden',
      email: 'drew.linden@minafter.com',
      phone: '614-555-8105',
      closingMode: 'Title / escrow closing',
      orderedBy: 'Buyer',
    },
    warranty: {
      status: 'Waived',
      orderedBy: 'Not ordered',
      provider: 'None',
      email: 'warranty.records@minafter.com',
    },
    hoa: {
      name: 'No homeowners association disclosed',
      delivery: 'No HOA document delivery is required',
    },
    contacts: {
      listingAgent: 'Leah Grant, Central Green Realty, leah.grant@minafter.com, 614-555-1205',
      buyersAgent: 'Caleb Young, Keystone Realty Group, caleb.young@minafter.com, 614-555-2205',
      loanOfficer: 'Nadia Wolfe, Patriot Home Lending, nadia.wolfe@minafter.com, 614-555-3205',
      attorney: 'Selena Ward, Ward Residential Law, selena.ward@minafter.com, 614-555-4205',
      inspector: 'Micah Fox, HearthCheck Inspections, micah.fox@minafter.com, 614-555-5205',
      appraiser: 'Dylan Marsh, Franklin County Appraisals, dylan.marsh@minafter.com, 614-555-6205',
    },
  },
  {
    acceptDate: '2026-06-29',
    id: 'TX-20260629-SYCAMORE',
    seller: {
      names: 'Eloise Hart and Shawn Hart',
      status: 'Married',
      address: '48 Winding Creek Boulevard, Lebanon, OH 45036',
      homePhone: '513-555-6107',
      workPhone: '513-555-6108',
      email: 'eloise.hart@minafter.com; shawn.hart@minafter.com',
    },
    buyer: {
      names: 'Devon Wallace',
      status: 'Single',
      address: '7210 Summit View Drive, Mason, OH 45040',
      homePhone: '513-555-7107',
      workPhone: '513-555-7108',
      email: 'devon.wallace@minafter.com',
    },
    property: {
      address: '9052 Sycamore Ridge',
      cityStateZip: 'Mason, OH 45040',
      county: 'Warren',
      parcel: '16-34-202-018',
      included: 'Kitchen appliances, basement media cabinet, pool equipment, window shades',
      excluded: "Seller's wine refrigerator, mounted artwork, patio heaters",
      leadPaint: 'No lead-based paint disclosure required because the home was built in 2007',
    },
    price: 612300,
    earnest: 15000,
    downPayment: 122460,
    loanAmount: 489840,
    financingType: 'Jumbo conventional mortgage',
    occupancy: 'Buyer intends to occupy the property as a primary residence',
    closingDays: 46,
    title: {
      company: 'Keystone Closing Group',
      contact: 'Rhea Novak',
      email: 'rhea.novak@minafter.com',
      phone: '513-555-8107',
      closingMode: 'Title / escrow closing',
      orderedBy: 'Seller',
    },
    warranty: {
      status: 'Included',
      orderedBy: 'Seller',
      provider: 'HavenGuard Warranty',
      email: 'havenguard.service@minafter.com',
    },
    hoa: {
      name: 'Parkmere Estates Association',
      delivery: 'Seller shall deliver HOA documents within seven (7) days of acceptance',
    },
    contacts: {
      listingAgent: 'June Porter, Queen City Realty, june.porter@minafter.com, 513-555-1207',
      buyersAgent: 'Mateo Cruz, Terrace Line Realty, mateo.cruz@minafter.com, 513-555-2207',
      loanOfficer: 'Ariel Marks, Premier Mortgage Partners, ariel.marks@minafter.com, 513-555-3207',
      attorney: 'Noel Richter, Richter Closing Law, noel.richter@minafter.com, 513-555-4207',
      inspector: 'Vera Knox, Foundation First Inspections, vera.knox@minafter.com, 513-555-5207',
      appraiser: 'Hugo Pierce, Warren Valuation Co., hugo.pierce@minafter.com, 513-555-6207',
    },
  },
  {
    acceptDate: '2026-07-02',
    id: 'TX-20260702-PRAIRIE',
    seller: {
      names: 'Mina Patel and Arjun Patel',
      status: 'Married',
      address: '1176 Rivergate Lane, Perrysburg, OH 43551',
      homePhone: '419-555-6109',
      workPhone: '419-555-6110',
      email: 'mina.patel@minafter.com; arjun.patel@minafter.com',
    },
    buyer: {
      names: 'Grace Alvarez and Mateo Alvarez',
      status: 'Married',
      address: '2040 Eastgate Road, Maumee, OH 43537',
      homePhone: '419-555-7109',
      workPhone: '419-555-7110',
      email: 'grace.alvarez@minafter.com; mateo.alvarez@minafter.com',
    },
    property: {
      address: '126 Prairie View Drive',
      cityStateZip: 'Perrysburg, OH 43551',
      county: 'Wood',
      parcel: 'P60-400-270402018000',
      included: 'Kitchen appliances, washer, dryer, irrigation controller, garage cabinets',
      excluded: "Seller's dining room chandelier, nursery mural, portable generator",
      leadPaint: 'No lead-based paint disclosure required because the home was built in 2012',
    },
    price: 374250,
    earnest: 9000,
    downPayment: 37425,
    loanAmount: 336825,
    financingType: 'Conventional mortgage with buyer home-sale contingency',
    occupancy: 'Buyer intends to occupy the property as a primary residence',
    closingDays: 47,
    title: {
      company: 'Maumee Valley Title',
      contact: 'Elian Cook',
      email: 'elian.cook@minafter.com',
      phone: '419-555-8109',
      closingMode: 'Title / escrow closing',
      orderedBy: 'Seller',
    },
    warranty: {
      status: 'Included',
      orderedBy: 'Buyer',
      provider: 'HomeSure Plus',
      email: 'homesure.plus@minafter.com',
    },
    hoa: {
      name: 'Prairie View Community Association',
      delivery: 'Seller shall deliver HOA documents within seven (7) days of acceptance',
    },
    contacts: {
      listingAgent: 'Anika West, Glass City Realty, anika.west@minafter.com, 419-555-1209',
      buyersAgent: 'Noah Benton, MetroField Realty, noah.benton@minafter.com, 419-555-2209',
      loanOfficer: 'Kira Dalton, Great Lakes Lending, kira.dalton@minafter.com, 419-555-3209',
      attorney: 'Ivy Booker, Booker Closing Counsel, ivy.booker@minafter.com, 419-555-4209',
      inspector: 'Gavin North, Wood County Home Check, gavin.north@minafter.com, 419-555-5209',
      appraiser: 'Mira Coleman, Maumee Appraisal Co., mira.coleman@minafter.com, 419-555-6209',
    },
    extraContingency: 'Buyer shall remove the home-sale contingency or provide evidence of a non-contingent closing on or before the survey review deadline.',
  },
  {
    acceptDate: '2026-07-06',
    id: 'TX-20260706-RIVERSTONE',
    seller: {
      names: 'Victor Chen',
      status: 'Single',
      address: '9084 Creek Meadow Loop, Hilliard, OH 43026',
      homePhone: '614-555-6111',
      workPhone: '614-555-6112',
      email: 'victor.chen@minafter.com',
    },
    buyer: {
      names: 'Amelia Brooks',
      status: 'Single',
      address: '380 West Spring Street Apt 6, Columbus, OH 43215',
      homePhone: '614-555-7111',
      workPhone: '614-555-7112',
      email: 'amelia.brooks@minafter.com',
    },
    property: {
      address: '8104 Riverstone Place',
      cityStateZip: 'Hilliard, OH 43026',
      county: 'Franklin',
      parcel: '050-011882-00',
      included: 'Range, refrigerator, dishwasher, built-in shelving, rain barrels',
      excluded: "Seller's standing desk, backyard planters, electric vehicle charger",
      leadPaint: 'No lead-based paint disclosure required because the home was built in 2001',
    },
    price: 455000,
    earnest: 20000,
    downPayment: 455000,
    loanAmount: 0,
    financingType: 'Cash purchase - proof of funds required',
    occupancy: 'Buyer intends to occupy the property as a primary residence',
    closingDays: 31,
    title: {
      company: 'Capital City Title',
      contact: 'Piper Sloan',
      email: 'piper.sloan@minafter.com',
      phone: '614-555-8111',
      closingMode: 'Title / escrow closing',
      orderedBy: 'Buyer',
    },
    warranty: {
      status: 'Included',
      orderedBy: 'Seller',
      provider: 'Neighborhood Home Warranty',
      email: 'neighborhood.warranty@minafter.com',
    },
    hoa: {
      name: 'Riverstone Residential Association',
      delivery: 'Seller shall deliver HOA documents within seven (7) days of acceptance',
    },
    contacts: {
      listingAgent: 'Sienna Cole, Central Nest Realty, sienna.cole@minafter.com, 614-555-1211',
      buyersAgent: 'Rory Finch, Foundry Realty, rory.finch@minafter.com, 614-555-2211',
      loanOfficer: 'Proof Funds Desk, Capital Verification Team, proof.funds@minafter.com, 614-555-3211',
      attorney: 'Alden Price, Price Closing Law, alden.price@minafter.com, 614-555-4211',
      inspector: 'Talia Snow, ClearBeam Inspections, talia.snow@minafter.com, 614-555-5211',
      appraiser: 'Cash Review Desk, Independent Value Review, cash.review@minafter.com, 614-555-6211',
    },
    cashTerms: true,
  },
  {
    acceptDate: '2026-07-09',
    id: 'TX-20260709-NORTHFIELD',
    seller: {
      names: 'Emmett Rivera and Tomas Rivera',
      status: 'Married',
      address: '404 Maple Ridge Drive, Kettering, OH 45429',
      homePhone: '937-555-6113',
      workPhone: '937-555-6114',
      email: 'emmett.rivera@minafter.com; tomas.rivera@minafter.com',
    },
    buyer: {
      names: 'Zoe Martin and Isaac Martin',
      status: 'Married',
      address: '1720 Patterson Road, Dayton, OH 45420',
      homePhone: '937-555-7113',
      workPhone: '937-555-7114',
      email: 'zoe.martin@minafter.com; isaac.martin@minafter.com',
    },
    property: {
      address: '473 Northfield Circle',
      cityStateZip: 'Dayton, OH 45459',
      county: 'Montgomery',
      parcel: 'O67-50210-0068',
      included: 'Kitchen appliances, washer, dryer, ring doorbell, shed',
      excluded: "Seller's patio swing, workshop tools, bedroom curtains",
      leadPaint: 'No lead-based paint disclosure required because the home was built in 1984',
    },
    price: 265000,
    earnest: 4500,
    downPayment: 9275,
    loanAmount: 255725,
    financingType: 'FHA mortgage',
    occupancy: 'Buyer intends to occupy the property as a primary residence',
    closingDays: 44,
    title: {
      company: 'Miami Valley Escrow',
      contact: 'Dana Lake',
      email: 'dana.lake@minafter.com',
      phone: '937-555-8113',
      closingMode: 'Title / escrow closing',
      orderedBy: 'Seller',
    },
    warranty: {
      status: 'Included',
      orderedBy: 'Seller',
      provider: 'HomeFirst Warranty',
      email: 'homefirst.service@minafter.com',
    },
    hoa: {
      name: 'Meadow View Neighborhood Association',
      delivery: 'Seller shall deliver HOA documents within seven (7) days of acceptance',
    },
    contacts: {
      listingAgent: 'Lara Beck, Miami Valley Realty, lara.beck@minafter.com, 937-555-1213',
      buyersAgent: 'Evan Rhodes, Keystone Door Realty, evan.rhodes@minafter.com, 937-555-2213',
      loanOfficer: 'Inez Vaughn, Dayton Home Finance, inez.vaughn@minafter.com, 937-555-3213',
      attorney: 'Roman Blake, Blake Settlement Law, roman.blake@minafter.com, 937-555-4213',
      inspector: 'Cora Flynn, Dayton Property Review, cora.flynn@minafter.com, 937-555-5213',
      appraiser: 'Mason Reed, Montgomery Valuation, mason.reed@minafter.com, 937-555-6213',
    },
  },
  {
    acceptDate: '2026-07-13',
    id: 'TX-20260713-QUARRY',
    seller: {
      names: 'Helena Ross',
      status: 'Single',
      address: '620 Grandin Road, Cincinnati, OH 45208',
      homePhone: '513-555-6115',
      workPhone: '513-555-6116',
      email: 'helena.ross@minafter.com',
    },
    buyer: {
      names: 'Peter Sullivan and Ana Sullivan',
      status: 'Married',
      address: '909 Ludlow Avenue, Cincinnati, OH 45220',
      homePhone: '513-555-7115',
      workPhone: '513-555-7116',
      email: 'peter.sullivan@minafter.com; ana.sullivan@minafter.com',
    },
    property: {
      address: '1901 Quarry Point Road',
      cityStateZip: 'Cincinnati, OH 45206',
      county: 'Hamilton',
      parcel: '055-0009-0185-00',
      included: 'Kitchen appliances, basement dehumidifier, built-in bookshelves, garden bench',
      excluded: "Seller's entry mirror, antique dining light, pottery kiln",
      leadPaint: 'Disclosure required because the home was built before 1978',
    },
    price: 488800,
    earnest: 10000,
    downPayment: 73320,
    loanAmount: 415480,
    financingType: 'Conventional renovation mortgage',
    occupancy: 'Buyer intends to occupy the property after completion of lender-approved renovation work',
    closingDays: 49,
    title: {
      company: 'Queen City Title Partners',
      contact: 'Selah Warren',
      email: 'selah.warren@minafter.com',
      phone: '513-555-8115',
      closingMode: 'Title / escrow closing',
      orderedBy: 'Buyer',
    },
    warranty: {
      status: 'Included',
      orderedBy: 'Buyer',
      provider: 'RenovateCare Warranty',
      email: 'renovatecare.service@minafter.com',
    },
    hoa: {
      name: 'No homeowners association disclosed',
      delivery: 'No HOA document delivery is required',
    },
    contacts: {
      listingAgent: 'Maeve Sutton, CitySteps Realty, maeve.sutton@minafter.com, 513-555-1215',
      buyersAgent: 'Otis Hale, Incline Realty, otis.hale@minafter.com, 513-555-2215',
      loanOfficer: 'Priam Wells, Renovation Mortgage Desk, priam.wells@minafter.com, 513-555-3215',
      attorney: 'Nina Frost, Frost Transfer Law, nina.frost@minafter.com, 513-555-4215',
      inspector: 'Dorian West, Historic Home Inspectors, dorian.west@minafter.com, 513-555-5215',
      appraiser: 'Carmen Vale, Hamilton Appraisal House, carmen.vale@minafter.com, 513-555-6215',
    },
    extraContingency: 'Renovation scope, contractor bid, and lender repair escrow approval must be accepted by Buyer on or before the financing deadline.',
  },
  {
    acceptDate: '2026-07-16',
    id: 'TX-20260716-BIRCHWOOD',
    seller: {
      names: 'Naomi Grant and Felix Grant',
      status: 'Married',
      address: '32 Old Mill Drive, Delaware, OH 43015',
      homePhone: '740-555-6117',
      workPhone: '740-555-6118',
      email: 'naomi.grant@minafter.com; felix.grant@minafter.com',
    },
    buyer: {
      names: 'Layla Foster',
      status: 'Single',
      address: '1594 Polaris Parkway Apt 22, Columbus, OH 43240',
      homePhone: '740-555-7117',
      workPhone: '740-555-7118',
      email: 'layla.foster@minafter.com',
    },
    property: {
      address: '620 Birchwood Trail',
      cityStateZip: 'Delaware, OH 43015',
      county: 'Delaware',
      parcel: '519-432-08-004-000',
      included: 'Kitchen appliances, washer, dryer, garage storage tracks, outdoor playset',
      excluded: "Seller's potted trees, basement freezer, electric fireplace insert",
      leadPaint: 'No lead-based paint disclosure required because the home was built in 2015',
    },
    price: 337600,
    earnest: 7500,
    downPayment: 33760,
    loanAmount: 303840,
    financingType: 'Conventional mortgage',
    occupancy: 'Buyer intends to occupy the property as a primary residence',
    closingDays: 41,
    title: {
      company: 'Capital City Title North',
      contact: 'Nico Flynn',
      email: 'nico.flynn@minafter.com',
      phone: '740-555-8117',
      closingMode: 'Title / escrow closing',
      orderedBy: 'Seller',
    },
    warranty: {
      status: 'Included',
      orderedBy: 'Seller',
      provider: 'NorthStar Home Warranty',
      email: 'northstar.claims@minafter.com',
    },
    hoa: {
      name: 'Birchwood Trail Community Association',
      delivery: 'Seller shall deliver HOA documents within seven (7) days of acceptance',
    },
    contacts: {
      listingAgent: 'Clara Wynn, Delaware Door Realty, clara.wynn@minafter.com, 740-555-1217',
      buyersAgent: 'Silas Dean, Porchlight Realty, silas.dean@minafter.com, 740-555-2217',
      loanOfficer: 'Tori Banks, Polaris Mortgage Group, tori.banks@minafter.com, 740-555-3217',
      attorney: 'Julian Rook, Rook Closing Counsel, julian.rook@minafter.com, 740-555-4217',
      inspector: 'Maren Page, Central Ohio Inspectors, maren.page@minafter.com, 740-555-5217',
      appraiser: 'Luca Blair, Delaware Appraisal Partners, luca.blair@minafter.com, 740-555-6217',
    },
  },
  {
    acceptDate: '2026-07-20',
    id: 'TX-20260720-LAKEPOINT',
    seller: {
      names: 'Theo Adams and Isabel Adams',
      status: 'Married',
      address: '18 Harbor Bend Drive, Avon Lake, OH 44012',
      homePhone: '440-555-6119',
      workPhone: '440-555-6120',
      email: 'theo.adams@minafter.com; isabel.adams@minafter.com',
    },
    buyer: {
      names: 'Riley Chen and Parker Chen',
      status: 'Married',
      address: '27830 Lake Road, Bay Village, OH 44140',
      homePhone: '440-555-7119',
      workPhone: '440-555-7120',
      email: 'riley.chen@minafter.com; parker.chen@minafter.com',
    },
    property: {
      address: '52 Lakepoint Terrace',
      cityStateZip: 'Avon Lake, OH 44012',
      county: 'Lorain',
      parcel: '04-00-039-116-002',
      included: 'Kitchen appliances, washer, dryer, dock locker, custom window treatments',
      excluded: "Seller's boat lift, outdoor sculpture, wine room inventory",
      leadPaint: 'No lead-based paint disclosure required because the home was built in 2009',
    },
    price: 699500,
    earnest: 20000,
    downPayment: 139900,
    loanAmount: 559600,
    financingType: 'Jumbo conventional mortgage',
    occupancy: 'Buyer intends to occupy the property as a primary residence',
    closingDays: 50,
    title: {
      company: 'Shoreline Title and Escrow',
      contact: 'Mara Finch',
      email: 'mara.finch@minafter.com',
      phone: '440-555-8119',
      closingMode: 'Title / escrow closing',
      orderedBy: 'Buyer',
    },
    warranty: {
      status: 'Included',
      orderedBy: 'Buyer',
      provider: 'LakeHome Warranty Services',
      email: 'lakehome.service@minafter.com',
    },
    hoa: {
      name: 'Lakepoint Terrace Association',
      delivery: 'Seller shall deliver HOA documents within seven (7) days of acceptance',
    },
    contacts: {
      listingAgent: 'Blair Sutton, Shore West Realty, blair.sutton@minafter.com, 440-555-1219',
      buyersAgent: 'Celia Knox, Lakefront Realty Group, celia.knox@minafter.com, 440-555-2219',
      loanOfficer: 'Graham Bell, Lake Mortgage Partners, graham.bell@minafter.com, 440-555-3219',
      attorney: 'Violet Nash, Nash Residential Law, violet.nash@minafter.com, 440-555-4219',
      inspector: 'Jon Reed, Shoreline Property Review, jon.reed@minafter.com, 440-555-5219',
      appraiser: 'Opal Mercer, Lorain Valuation Co., opal.mercer@minafter.com, 440-555-6219',
    },
  },
]

function toDate(isoDate) {
  const [year, month, day] = isoDate.split('-').map(Number)
  return new Date(Date.UTC(year, month - 1, day))
}

function addDays(isoDate, days) {
  const date = toDate(isoDate)
  date.setUTCDate(date.getUTCDate() + days)
  return date.toISOString().slice(0, 10)
}

function longDate(isoDate) {
  return new Intl.DateTimeFormat('en-US', {
    month: 'long',
    day: 'numeric',
    year: 'numeric',
    timeZone: 'UTC',
  }).format(toDate(isoDate))
}

function compactDate(isoDate) {
  return isoDate.replaceAll('-', '')
}

function money(amount) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount)
}

function buildDates(transaction) {
  const acceptDate = transaction.acceptDate
  const closingDate = addDays(acceptDate, transaction.closingDays)
  return {
    acceptDate,
    earnestDue: addDays(acceptDate, 3),
    loanApplicationDue: addDays(acceptDate, 5),
    proofFundsDue: addDays(acceptDate, 2),
    inspectionDeadline: addDays(acceptDate, 7),
    hoaDeadline: transaction.hoa.name.startsWith('No homeowners') ? 'Not applicable' : addDays(acceptDate, 7),
    inspectionResponseDeadline: addDays(acceptDate, 9),
    surveyReviewDeadline: addDays(acceptDate, 12),
    financingDeadline: transaction.cashTerms ? 'Not applicable - cash transaction' : addDays(acceptDate, 24),
    appraisalDate: transaction.cashTerms ? addDays(acceptDate, 18) : addDays(acceptDate, 31),
    insuranceBinderDue: addDays(acceptDate, 34),
    closingDate,
    finalWalkThrough: addDays(closingDate, -1),
    possessionDate: addDays(closingDate, 2),
  }
}

function buildSections(transaction) {
  const dates = buildDates(transaction)
  const financingParagraphs = transaction.cashTerms
    ? [
        `Buyer shall provide written proof of immediately available funds on or before ${longDate(dates.proofFundsDue)}. The transaction is not contingent on Buyer obtaining a mortgage loan, but Buyer may order an optional appraisal for personal review on or before ${longDate(dates.appraisalDate)}.`,
        `Buyer shall provide evidence of homeowner insurance commitment on or before ${longDate(dates.insuranceBinderDue)}. Failure to obtain financing shall not be a basis for terminating this cash agreement.`,
      ]
    : [
        `Buyer shall make written loan application within five (5) calendar days after the Contract Acceptance Date. Buyer shall obtain loan approval on or before ${longDate(dates.financingDeadline)}. If Buyer cannot obtain loan approval despite good-faith efforts, Seller may extend the deadline in writing or the agreement may be terminated according to the earnest money provisions.`,
        `The lender-ordered appraisal is expected on or before ${longDate(dates.appraisalDate)}. Buyer shall provide evidence of homeowner insurance commitment on or before ${longDate(dates.insuranceBinderDue)}.`,
      ]

  const additionalRows = [
    ['Survey review', `Buyer may review a survey or mortgage location survey on or before ${longDate(dates.surveyReviewDeadline)}`],
    ['Final walk-through', `Buyer may complete a final walk-through on or before ${longDate(dates.finalWalkThrough)}`],
    ['Lead-based paint', transaction.property.leadPaint],
  ]

  if (transaction.extraContingency) additionalRows.push(['Special contingency', transaction.extraContingency])

  const dateSummaryRows = [
    ['Contract acceptance date', longDate(dates.acceptDate)],
    ['Earnest money due', longDate(dates.earnestDue)],
    [transaction.cashTerms ? 'Proof of funds due' : 'Loan application due', longDate(transaction.cashTerms ? dates.proofFundsDue : dates.loanApplicationDue)],
    ['Inspection deadline', longDate(dates.inspectionDeadline)],
    ['HOA documents deadline', dates.hoaDeadline === 'Not applicable' ? dates.hoaDeadline : longDate(dates.hoaDeadline)],
    ['Inspection response deadline', longDate(dates.inspectionResponseDeadline)],
    ['Survey review deadline', longDate(dates.surveyReviewDeadline)],
    ['Financing deadline', typeof dates.financingDeadline === 'string' && dates.financingDeadline.startsWith('Not applicable') ? dates.financingDeadline : longDate(dates.financingDeadline)],
    [transaction.cashTerms ? 'Optional appraisal deadline' : 'Appraisal expected date', longDate(dates.appraisalDate)],
    ['Insurance binder due', longDate(dates.insuranceBinderDue)],
    ['Final walk-through', longDate(dates.finalWalkThrough)],
    ['Closing date', longDate(dates.closingDate)],
    ['Possession date', longDate(dates.possessionDate)],
  ]

  return [
    {
      heading: '1.0 SELLER INFORMATION',
      rows: [
        ['Seller(s)', transaction.seller.names],
        ['Marital status', transaction.seller.status],
        ['Current address', transaction.seller.address],
        ['Home phone', transaction.seller.homePhone],
        ['Work phone', transaction.seller.workPhone],
        ['Email', transaction.seller.email],
      ],
    },
    {
      heading: '1.1 BUYER INFORMATION',
      rows: [
        ['Buyer(s)', transaction.buyer.names],
        ['Marital status', transaction.buyer.status],
        ['Current address', transaction.buyer.address],
        ['Home phone', transaction.buyer.homePhone],
        ['Work phone', transaction.buyer.workPhone],
        ['Email', transaction.buyer.email],
      ],
    },
    {
      heading: '2.0 PROPERTY',
      rows: [
        ['Property address', transaction.property.address],
        ['City, state, ZIP', transaction.property.cityStateZip],
        ['County', transaction.property.county],
        ['Permanent parcel / tax ID', transaction.property.parcel],
        ['Also included', transaction.property.included],
        ['Not included', transaction.property.excluded],
      ],
    },
    {
      heading: '3.0 PRICE AND FINANCING',
      rows: [
        ['Purchase price', money(transaction.price)],
        ['Earnest money deposit', `${money(transaction.earnest)}, payable to escrow within 3 days of acceptance`],
        ['Anticipated down payment', money(transaction.downPayment)],
        ['Anticipated loan amount', money(transaction.loanAmount)],
        ['Financing type', transaction.financingType],
        ['Owner occupancy', transaction.occupancy],
      ],
    },
    {
      heading: '4.0 FINANCING CONTINGENCY',
      paragraphs: financingParagraphs,
    },
    {
      heading: '5.0 CLOSING AND ESCROW',
      rows: [
        ['Escrow / title company', transaction.title.company],
        ['Title contact', transaction.title.contact],
        ['Title email', transaction.title.email],
        ['Title phone', transaction.title.phone],
        ['Closing mode', transaction.title.closingMode],
        ['Title ordered by', transaction.title.orderedBy],
        ['Contract acceptance date', longDate(dates.acceptDate)],
        ['Closing date', longDate(dates.closingDate)],
        ['Possession date', longDate(dates.possessionDate)],
        ['Possession time', '5:00 PM'],
        ['Holdover rent', '$150.00 per day after possession date'],
      ],
    },
    {
      heading: '6.0 TITLE, PRORATIONS, AND CHARGES',
      paragraphs: [
        'Seller shall convey marketable and insurable title by general warranty deed, free and clear of liens except permitted exceptions of record. Seller shall pay the title exam, owner title policy premium, deed preparation, lien discharge costs, transfer tax, conveyance fees, and public authority inspection certificates required of Seller.',
        'Buyer shall pay costs incident to Buyer obtaining financing, the lender policy, deed and mortgage recording fees, inspection costs requested by Buyer, and any mortgage location survey required by the lender. For a cash transaction, Buyer shall instead pay escrow and recording costs assigned to Buyer by this agreement.',
      ],
    },
    {
      heading: '7.0 HOME WARRANTY AND HOA',
      rows: [
        ['Home warranty', transaction.warranty.status],
        ['Warranty ordered by', transaction.warranty.orderedBy],
        ['Warranty provider', transaction.warranty.provider],
        ['Warranty email', transaction.warranty.email],
        ['HOA', transaction.hoa.name],
        ['HOA document delivery', transaction.hoa.delivery],
        ['HOA document deadline', dates.hoaDeadline === 'Not applicable' ? dates.hoaDeadline : longDate(dates.hoaDeadline)],
      ],
    },
    {
      heading: '8.0 CONDITION OF PROPERTY AND INSPECTION',
      paragraphs: [
        'Buyer acknowledges that Buyer has been advised to engage, at Buyer expense, a professional property inspector to inspect the property and improvements. Buyer will have a home inspection.',
        `The general home inspection must be completed on or before ${longDate(dates.inspectionDeadline)}. Buyer shall approve, disapprove, or request repairs in writing no later than ${longDate(dates.inspectionResponseDeadline)}. If the inspection results are not satisfactory and the parties do not reach a written resolution within the time specified, escrow shall return the earnest money deposit to Buyer and this agreement shall become null and void.`,
      ],
    },
    {
      heading: '9.0 ADDITIONAL CONTINGENCIES',
      rows: additionalRows,
    },
    {
      heading: '10.0 CONTACT DIRECTORY ADDENDUM',
      rows: [
        ['Fixture transaction ID', transaction.id],
        ['Listing agent', transaction.contacts.listingAgent],
        ["Buyer's agent", transaction.contacts.buyersAgent],
        ['Loan officer / funds contact', transaction.contacts.loanOfficer],
        ['Title / escrow rep', `${transaction.title.contact}, ${transaction.title.company}, ${transaction.title.email}, ${transaction.title.phone}`],
        ['Closing attorney', transaction.contacts.attorney],
        ['Inspector', transaction.contacts.inspector],
        ['Appraiser', transaction.contacts.appraiser],
      ],
    },
    {
      heading: '11.0 DATE SUMMARY FOR TESTING',
      rows: dateSummaryRows,
    },
    {
      heading: '12.0 BINDING AGREEMENT',
      paragraphs: [
        'Acceptance of this offer and any attached addenda shall create a legal agreement binding on Buyer and Seller and their heirs, executors, administrators, successors, and assigns. All amendments, addenda, and other alterations must be in writing, dated, and signed by both Buyer and Seller.',
        'This fixture intentionally leaves the original signature section unsigned. Use it to test the AI wizard signature review, e-signature queue decision, Active Transactions card, and transaction detail workspace.',
      ],
    },
  ]
}

function escapePdfText(text) {
  return text
    .replaceAll('\\', '\\\\')
    .replaceAll('(', '\\(')
    .replaceAll(')', '\\)')
}

function widthOf(text, size) {
  let width = 0
  for (const char of text) {
    if (char === ' ') width += 0.28
    else if ('ilI.,;:!|[]'.includes(char)) width += 0.24
    else if ('mwMW'.includes(char)) width += 0.82
    else if ('ABCDEFGHJKLMNOPQRSTUVWXYZ'.includes(char)) width += 0.63
    else if ('0123456789'.includes(char)) width += 0.52
    else width += 0.5
  }
  return width * size
}

function wrapText(text, size, width) {
  const words = text.split(/\s+/).filter(Boolean)
  const lines = []
  let line = ''

  for (const word of words) {
    const candidate = line ? `${line} ${word}` : word
    if (line && widthOf(candidate, size) > width) {
      lines.push(line)
      line = word
    } else {
      line = candidate
    }
  }

  if (line) lines.push(line)
  return lines
}

function renderPdf(transaction, output) {
  const sections = buildSections(transaction)
  const pages = []
  let current = []
  let y = topY
  let pageNo = 0

  function addRaw(raw) {
    current.push(raw)
  }

  function addText(text, x, yPos, size = 9.4, font = 'F1') {
    addRaw(`BT /${font} ${size.toFixed(2)} Tf ${x.toFixed(2)} ${yPos.toFixed(2)} Td (${escapePdfText(text)}) Tj ET`)
  }

  function addRule(x1, y1, x2, y2, width = 0.7) {
    addRaw(`${width.toFixed(2)} w ${x1.toFixed(2)} ${y1.toFixed(2)} m ${x2.toFixed(2)} ${y2.toFixed(2)} l S`)
  }

  function addHeader() {
    pageNo += 1
    const titleSize = pageNo === 1 ? 15 : 10.5
    const titleX = Math.max(marginX, (pageWidth - widthOf(title, titleSize)) / 2)
    addText(title, titleX, topY, titleSize, 'F2')
    const subSize = 8.5
    const subX = Math.max(marginX, (pageWidth - widthOf(subtitle, subSize)) / 2)
    addText(subtitle, subX, topY - 15, subSize, 'F1')
    addText(`Fixture ${transaction.id}`, marginX, bottomY - 20, 8, 'F1')
    addText(`Page ${pageNo}`, pageWidth - marginX - 32, bottomY - 20, 8, 'F1')
    y = topY - 36
  }

  function newPage() {
    pages.push(current.join('\n'))
    current = []
    addHeader()
  }

  function ensure(space) {
    if (y - space < bottomY) newPage()
  }

  function addWrapped(text, options = {}) {
    const size = options.size ?? 9.4
    const font = options.font ?? 'F1'
    const x = options.x ?? marginX
    const width = options.width ?? maxWidth
    const lineHeight = options.lineHeight ?? 11.6
    const lines = wrapText(text, size, width)
    ensure(lines.length * lineHeight + (options.after ?? 4))
    for (const line of lines) {
      addText(line, x, y, size, font)
      y -= lineHeight
    }
    y -= options.after ?? 4
  }

  function addRow(label, value) {
    const labelWidth = 142
    const lines = wrapText(String(value), 9.2, maxWidth - labelWidth - 10)
    ensure(Math.max(lines.length, 1) * 11.2 + 3)
    addText(`${label}:`, marginX, y, 9.2, 'F2')
    for (let i = 0; i < lines.length; i += 1) {
      addText(lines[i], marginX + labelWidth, y - i * 11.2, 9.2, 'F1')
    }
    y -= Math.max(lines.length, 1) * 11.2 + 2
  }

  function addSection(section) {
    ensure(28)
    addWrapped(section.heading, { size: 9.8, font: 'F2', lineHeight: 12, after: 2 })
    if (section.rows) {
      for (const [label, value] of section.rows) addRow(label, value)
    }
    if (section.paragraphs) {
      for (const paragraph of section.paragraphs) addWrapped(paragraph)
    }
    y -= 4
  }

  function addSignatureBlocks() {
    ensure(250)
    addWrapped('13.0 SIGNATURE SECTION', { size: 10, font: 'F2', after: 8 })
    addWrapped('Original signature marks were removed. Each signature and printed-name field below is an underlined blank space for testing unsigned-document handling.', { size: 9.2, after: 12 })

    const leftX = marginX
    const rightX = marginX + 300
    const lineLen = 210
    const rowGap = 42

    addText('BUYER(S) SIGNATURE', leftX, y, 9.2, 'F2')
    addText('PRINT NAME', rightX, y, 9.2, 'F2')
    y -= 22
    for (let i = 1; i <= 2; i += 1) {
      addText(`${i})`, leftX, y + 3, 9.2, 'F1')
      addRule(leftX + 18, y, leftX + lineLen, y, 0.8)
      addRule(rightX, y, rightX + lineLen, y, 0.8)
      y -= rowGap
    }
    addText('DATED:', leftX, y + 3, 9.2, 'F2')
    addRule(leftX + 44, y, leftX + 180, y, 0.8)
    addText('TIME:', rightX, y + 3, 9.2, 'F2')
    addRule(rightX + 38, y, rightX + 170, y, 0.8)
    y -= 46

    addText('SELLER(S) SIGNATURE', leftX, y, 9.2, 'F2')
    addText('PRINT NAME', rightX, y, 9.2, 'F2')
    y -= 22
    for (let i = 1; i <= 2; i += 1) {
      addText(`${i})`, leftX, y + 3, 9.2, 'F1')
      addRule(leftX + 18, y, leftX + lineLen, y, 0.8)
      addRule(rightX, y, rightX + lineLen, y, 0.8)
      y -= rowGap
    }
    addText('DATED:', leftX, y + 3, 9.2, 'F2')
    addRule(leftX + 44, y, leftX + 180, y, 0.8)
    addText('TIME:', rightX, y + 3, 9.2, 'F2')
    addRule(rightX + 38, y, rightX + 170, y, 0.8)
    y -= 30
  }

  addHeader()
  for (const section of sections) addSection(section)
  addSignatureBlocks()
  pages.push(current.join('\n'))

  const objects = []
  function reserveObject() {
    objects.push(null)
    return objects.length
  }
  function addObject(content) {
    objects.push(content)
    return objects.length
  }

  const catalogId = reserveObject()
  const pagesId = reserveObject()
  const fontRegularId = addObject('<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>')
  const fontBoldId = addObject('<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>')
  const pageIds = []

  for (const content of pages) {
    const length = Buffer.byteLength(content, 'latin1')
    const contentId = addObject(`<< /Length ${length} >>\nstream\n${content}\nendstream`)
    const pageId = addObject(`<< /Type /Page /Parent ${pagesId} 0 R /MediaBox [0 0 ${pageWidth} ${pageHeight}] /Resources << /Font << /F1 ${fontRegularId} 0 R /F2 ${fontBoldId} 0 R >> >> /Contents ${contentId} 0 R >>`)
    pageIds.push(pageId)
  }

  objects[catalogId - 1] = `<< /Type /Catalog /Pages ${pagesId} 0 R >>`
  objects[pagesId - 1] = `<< /Type /Pages /Kids [${pageIds.map((id) => `${id} 0 R`).join(' ')}] /Count ${pageIds.length} >>`

  let pdf = '%PDF-1.4\n%\xE2\xE3\xCF\xD3\n'
  const offsets = [0]
  for (let i = 0; i < objects.length; i += 1) {
    offsets.push(Buffer.byteLength(pdf, 'latin1'))
    pdf += `${i + 1} 0 obj\n${objects[i]}\nendobj\n`
  }
  const xrefOffset = Buffer.byteLength(pdf, 'latin1')
  pdf += `xref\n0 ${objects.length + 1}\n`
  pdf += '0000000000 65535 f \n'
  for (let i = 1; i < offsets.length; i += 1) {
    pdf += `${offsets[i].toString().padStart(10, '0')} 00000 n \n`
  }
  pdf += `trailer\n<< /Size ${objects.length + 1} /Root ${catalogId} 0 R >>\nstartxref\n${xrefOffset}\n%%EOF\n`

  fs.writeFileSync(output, Buffer.from(pdf, 'latin1'))
  return pages.length
}

fs.mkdirSync(outputDir, { recursive: true })

for (const transaction of transactions) {
  const output = path.join(outputDir, `transaction${compactDate(transaction.acceptDate)}.pdf`)
  const pages = renderPdf(transaction, output)
  console.log(`Wrote ${output} (${pages} pages)`)
}
