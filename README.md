# Clipeus Virtutis | Global B2B Sustainable Bio-Products Trade Portal

Official enterprise B2B trade & wholesale procurement platform for **Clipeus Virtutis**, commercializing certified multi-sector commodities, agro-products, and sustainable bio-innovations verified under NABL Accredited ISO/IEC 17025:2017 standards.

---

## 🏛️ Unique Brand Concept: The Roman Shield of Virtue (*Clipeus Virtutis*)

Awarded to Augustus by the Roman Senate in 27 BC, the *Clipeus Virtutis* honored four cardinal virtues. On this platform, they are translated into four concrete risk-mitigation shields for international trade buyers:

1. **VIRTUS (Technical Valor & Quality)**: Zero-defect assurance. Pre-shipment laboratory assays conducted in ISO/IEC 17025 accredited labs (0% charcoal, >94% alpha-cellulose purity, zero pathogens).
2. **IUSTITIA (Commercial Justice)**: Direct factory-gate FOB/CIF landed cost models eliminating middleman markups while ensuring equitable compensation to agrarian waste collectors.
3. **CLEMENTIA (Ecological Stewardship)**: Diverting 100+ tons of municipal vegetable waste, crop residues, and sacred temple floral offerings from landfills into carbon-negative building blocks and bio-fertilizers.
4. **PIETAS (Duty to Delivery)**: Guaranteed container loading slots at Port of Chennai, pre-cleared phytosanitary inspection certificates, and strict Incoterms 2020 adherence.

---

## 📄 Platform Directory (All 8 Pages & Clean URL Routing)

| Route / File | Description & Unique Capabilities |
|---|---|
| **`/` (`index.html`)** | **Home Portal**: Editorial hero still-life showcase, Interactive Roman Shield of Virtue widget, 8-product portfolio grid, film documentary player, and exhibition photo lightbox. |
| **`/products` (`products.html`)** | **Dedicated Trade Catalog**: Full B2B specifications, Interactive **TDS & COA Laboratory Dossier Modal**, **Container Capacity & Freight Estimator** (20ft FCL vs 40ft HC live payload simulation), and One-Click **Lab Sample Pack Requests**. |
| **`/about` (`about.html`)** | **About Us**: Comprehensive history of the Roman Shield of Virtue, ISO/IEC 17025 accredited laboratory testing nexus, Mission/Vision/Values/Commitment, and live global metrics (50+ Associates, 20+ Countries, 100+ Products, 50k+ Users). |
| **`/solutions` (`solutions.html`)** | **Trade Solutions**: 12 core enterprise capabilities (Trading Solutions, Supply Chain Support, Procurement, Import/Export, Quality Assurance, Fast Delivery, Warehouse Logistics, Inventory Management, Custom Formulations, Market Intelligence, Compliance, Digital Transformation). |
| **`/services` (`services.html`)** | **B2B Services**: 6 core service pillars, structured 4-step procurement workflow, and verified client endorsements. |
| **`/partners` (`partners.html`)** | **Chamber Alliances**: Official apex business federations: **SICCI**, **CII**, **FICCI**, **MCCI**, **MMA**, and **TNRISE**; 4 partnership categories; distributor application form. |
| **`/blog` (`blog.html`)** | **Market Intelligence**: 6 in-depth trade reports with interactive modal reader covering global trade 2026 trends, supply chain optimization, import/export regulations, and green logistics. |
| **`/contact` (`contact.html`)** | **Chennai Trade HQ & RFQ Desk**: Platinum Tower, Old Trunk Road, Pallavaram, Chennai; direct phone `+91 7299249907`, interactive map, and formal quotation desk. |

---

## 📦 Slide-Over RFQ Docket Drawer (`shared.js`)

- Available across all pages from top bar, navbar, product cards, and footers.
- Retains selected commercial products and sample kits across sessions via `localStorage`.
- Self-contained inquiry form: Company, Corporate Email, Phone, Estimated Volume, Incoterms 2020 (CIF/FOB/DDP/EXW), Destination Discharge Port, and Sample Kit inclusion.
- Generates instant docket reference IDs (e.g. `CV-RFQ-2026-XXXX`) with printable PDF receipts.

---

## 🚀 Running Locally

```bash
# Start local clean-URL server (running on port 8000)
./start.sh
# or
python3 server.py
```

Preview at: `http://localhost:8000` (supports both clean URLs `/products`, `/about` and `.html` extensions).

---

**Platform Architecture & Engineering**: Powered by [Kronixtech](https://kronixtech.in).
