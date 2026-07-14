# PHASE 3.1 — FORENSIC INVESTIGATION REPORT

**Date:** 2026-07-11 21:42 UTC
**Investigator:** AstroSage Document Intelligence Laboratory
**Objective:** Validate the Phase 3 claim that 'the corpus contains zero fully scanned PDFs.'

---

## Executive Summary

**VERDICT: DISPROVED**

The claim that the AstroSage corpus contains zero fully scanned PDFs is **DISPROVED**.

Multi-signal page-level analysis of **589 PDFs** (79,078 sampled pages) reveals:

- **51.4%** of all pages are scanned images
- **11.8%** of all pages contain OCR overlays (scanned + invisible text)
- **36.1%** of all pages contain native digital text
- **259 documents** are classified as fully scanned
- **39 documents** are classified as OCR overlay
- **20 documents** contain mixed scanned and native pages

**The original Phase 3 classifier was fundamentally incorrect.**
The Phase 3 classifier relied solely on `page.get_text()` which extracts any text layer —
including invisible OCR text overlaid on scanned images. This caused OCR-overlaid scans
to be misclassified as native text.

---

## Methodology

### Multi-Signal Page Classifier

Every page in every PDF was analyzed using **11+ independent signals**:

| Signal | Description |
|--------|-------------|
| Text layer exists | Whether `page.get_text()` returns content |
| Text character density | Characters per unit area |
| Font count | Number of distinct fonts |
| Font types | CID fonts, standard fonts, custom fonts |
| Image count | Number of embedded raster images |
| Image coverage % | Percentage of page area covered by images |
| Raster DPI | Estimated DPI of embedded images |
| Vector object count | Number of vector paths/lines |
| Text/image overlap | Whether text bounding boxes overlap image areas |
| OCR layer detection | Detection of invisible text on scanned images |
| Whitespace ratio | Ratio of whitespace to content |

### Classification Categories

| Class | Definition |
|-------|-----------|
| native_text | Born-digital text, no significant images |
| scanned_image | Image-only page (photo/scan), possibly with invisible OCR text |
| ocr_overlay | Image + embedded invisible text layer |
| mixed_content | Both text and significant images |
| blank | Empty or near-empty page |

---

## Page-Level Results

**Total pages sampled:** 79,078

| Classification | Count | Percentage |
|---------------|-------|------------|
| scanned_image | 40,678 | 51.4% |
| native_text | 28,520 | 36.1% |
| ocr_overlay | 9,290 | 11.7% |
| blank | 401 | 0.5% |
| mixed_content | 189 | 0.2% |

---

## Document-Level Results

**Total documents analyzed:** 589

| Classification | Count | Percentage |
|---------------|-------|------------|
| scanned_image | 259 | 44.0% |
| native_text | 226 | 38.4% |
| timeout | 42 | 7.1% |
| ocr_overlay | 39 | 6.6% |
| hybrid | 20 | 3.4% |
| mixed_content | 2 | 0.3% |
| error | 1 | 0.2% |

---

## Fully Scanned Documents

**259 documents** are classified as fully scanned:

| Document | Pages |
|----------|-------|
| महाभारत (Vol-1 to 12) गोरखपुर प्रेस.pdf | 7250 |
| 108-upanishads-with-upanishad-brahmam-commentary.pdf | 3580 |
| 2015.327535.Shrimad-Bhagwad.pdf | 1538 |
| test_download.pdf | 1538 |
| Gita-Sadhale.pdf | 1495 |
| Kalika Puran.pdf | 1400 |
| vayu-puran.pdf | 1160 |
| vayu puran by ramprashad.pdf | 1160 |
| स्कन्द पुराण.pdf | 1109 |
| sakand-puran.pdf | 1108 |
| Bhaktmal.pdf | 1035 |
| vayu puran banaras.pdf | 1018 |
| श्रीभक्तमाल.pdf | 1006 |
| padam-puran (1).pdf | 1001 |
| bhagwat-puran (1).pdf | 977 |
| Agni_Puran_of_Maharshi_Vyas_Mansukh_Ray_Mor_Guru_Mandal_Gran | 888 |
| अग्नि पुराण.pdf | 843 |
| agni-puran (2).pdf | 842 |
| Brahm Vaivart Puran 2.pdf | 824 |
| शिव पुराण.pdf | 813 |
| anandramayan.pdf | 811 |
| BhaiBaleWaliJanamSakhi.pdf | 797 |
| BhaiBaleWaliJanamSakhiPunjabi.pdf | 797 |
| ब्रह्म वैवर्त पुराण.pdf | 797 |
| vaivtpuran (1).pdf | 796 |
| नारद पुराण.pdf | 752 |
| nard-puran (1).pdf | 751 |
| Brahma-Sphuta-Siddhanta_VOL_I.pdf | 740 |
| Yogi Kathamrita.pdf | 736 |
| Hindi Book-Devi Bhagvat Puran.pdf | 722 |
| Devi Bhagvat Puran.pdf | 722 |
| 2015.553830.Bhrigu-Sanhita.pdf | 714 |
| 2015.341974.99999990234752.pdf | 704 |
| chanakyasutrani-skt-text-with-hindi-commentary-1946.pdf | 691 |
| 2015.540437.Sushrut-Sanhita.pdf | 663 |
| panini_Mahabhashya_I.pdf | 660 |
| Ling Puran Sans Eng 1.pdf | 642 |
| charaksamhitaatridevajigupt-vol-1.pdf | 639 |
| 2015.342017.99999990234792.pdf | 622 |
| Brahma Sutras - According to Sri Sankara by Swami Vireswaran | 614 |
| Skand puran 2.pdf | 611 |
| Vaman Puran.pdf | 610 |
| Brahma-Sphuta-Siddhanta_VOL_III.pdf | 600 |
| Ashtadhyayi_Padanukram_Kosh_016112_std.pdf | 600 |
| Shiv Puran 2.pdf | 600 |
| SHAKTA PRAMOD TANTRA.pdf | 599 |
| PU010-BrahmaPuranamu-1To3.pdf | 594 |
| Brahma-Sphuta-Siddhanta_VOL_II.pdf | 586 |
| Brahma-Sphuta-Siddhanta_VOL_IV.pdf | 586 |
| panini_Kosha_Dictionary of the Sanskrit.pdf | 581 |
| श्री गणेश पुराण.pdf | 562 |
| Shiv Puran 4.pdf | 553 |
| panchatantrasanskrithindi-jpmishra1910.pdf | 536 |
| विष्णु पुराण.pdf | 536 |
| vishnu-puran (1).pdf | 535 |
| गरुड पुराण.pdf | 529 |
| garuda1 (1).pdf | 528 |
| basava-puranam-telugu.pdf | 520 |
| Ling Puran 1.pdf | 518 |
| instapdf.in-bhavishya-malika-book-691.pdf | 517 |
| मत्स्य पुराण 1.pdf | 497 |
| matsya-puran-1 (1).pdf | 496 |
| matsya-puran-2 (1).pdf | 488 |
| मत्स्य पुराण 2.pdf | 488 |
| Shiv Puran 1.pdf | 479 |
| brahamandp (1).pdf | 477 |
| 006_Arun_Sanhita_Lal_Kitab_Hare_Krishna_Trashta.pdf | 467 |
| panini_Mahabhashya_IV.pdf | 467 |
| भविष्य पुराण.pdf | 449 |
| bavishya-puran (1).pdf | 448 |
| Kalika-Puran.pdf | 442 |
| panini_Mahabhashya_V.pdf | 441 |
| Skand puran 9.pdf | 430 |
| Shrimad bhagwat geeta.pdf | 428 |
| ब्रम्हा पुराण.pdf | 424 |
| bramha (1).pdf | 423 |
| vedant-darshan-brahmasutra-sanskrit-hindi.pdf | 417 |
| Narayaneeyam Bhagavata Condensed Of Meppathur Narayana Bhatt | 416 |
| brahamand (1).pdf | 416 |
| Vrddhayavanjataka of Minaraja 2 (2).pdf | 411 |
| कूर्म पुराण.pdf | 399 |
| 1hFBrGP2e8hyd1wmah5YaWfVE6wQZWevL_210828_120700.pdf | 398 |
| kurma (1).pdf | 398 |
| वराह पुराण.pdf | 393 |
| varaha-puran (1).pdf | 392 |
| ling (1).pdf | 390 |
| Hindi Book-Astanga-hrdayam.pdf | 387 |
| Mantra Rahasya.pdf | 384 |
| nity-karm-puja-prakash.pdf | 382 |
| WG989-1988 -Hanumad Rahasyam.pdf | 356 |
| WG463-1981-AkashBhairavaKalpamOfUmaMaheshwara.pdf | 345 |
| 2015.342310.Sugam-Jyotish.pdf | 344 |
| Skand puran 1.pdf | 325 |
| Skand puran 6.pdf | 310 |
| 235056697-Rudrayamala-tantram-रुद-रयामल-तन-त-रम (1).pdf | 306 |
| नरसिंह पुराण.pdf | 299 |
| markende-puran (1).pdf | 296 |
| 2015.342293.Sachitra-Jyotish.pdf | 296 |
| panini_Mahabhashya_III.pdf | 295 |
| chakra-mahavijnan.pdf | 288 |
| Ragachikitsa.pdf | 287 |
| Skand puran 5.pdf | 280 |
| vastu shastra hindi.pdf | 276 |
| कल्की पुराण.pdf | 260 |
| RekhaganitaVOL_II_DLI.pdf | 259 |
| 3374.pdf | 254 |
| Kamasutra of Vatsyayan with Hindi Trans. by Ramanand Sharma  | 248 |
| ಬೃಹಜ್ಜಾತಕ ಕನ್ನಡ.pdf | 248 |
| ravan-samhita-3.pdf | 245 |
| Sri Vidya Nityarchan Saparrya Paddhati - Pt. Hari Om Shukla. | 245 |
| panini_Ashtadhyayi_book1.pdf | 233 |
| Hinduo Ke Riti Riwaj Tatha Manyatayein (Hindi).pdf | 224 |
| panini_Ashtadhyayi_book5.pdf | 221 |
| HindiBook-shiva-samhita.pdf | 216 |
| ShivaSahinta_WithHindiTika.pdf | 216 |
| Shiva_Sahinta_WithHindiTika.pdf | 216 |
| Vigyan bhairav (bapulal).pdf | 213 |
| panini_Ashtadhyayi_book7.pdf | 205 |
| Guru Sadhana (1).pdf | 201 |
| ಸಂಪೂರ್ಣ ಋಗ್ವೇದ ಕನ್ನಡ .pdf | 199 |
| Sandhyaa Rahasya  Pt chamupati.pdf | 197 |
| वामन पुराण.pdf | 197 |
| vamanpuran (1).pdf | 196 |
| Shata-Chakra-Nirupana-of-Shree-Purnananda-Yati-Goswami-Prahl | 187 |
| 2015.539126.Indrajal.pdf | 186 |
| 2015.545358.Ank-Vidya.pdf | 186 |
| हिमालय के योगियों की गुप्त सिद्धियां .pdf | 179 |
| 2015.538690.Ratna-Parichay.pdf | 162 |
| vivakchudamani.pdf | 161 |
| panini_Ashtadhyayi_book2.pdf | 161 |
| हस्तरेखा विज्ञान और पंचांगुली साधना.pdf | 160 |
| instapdf.in-kamasutra-132.pdf | 160 |
| Jyotish Mein Svara Vigyan Ka Mahatva - Kedar Nath Joshi.pdf | 148 |
| ಮಹಾಭಾರತದ ಆದರ್ಶ_.pdf | 142 |
| Kundalini Yog - Dr. Rakesh Giri.pdf | 138 |
| karthikapuranam.pdf | 137 |
| 2015.378893.Bhartiya-Jyotish.pdf | 134 |
| Bhavishya-Malika-in-Hindi.pdf | 130 |
| Copy of मीरा बाई का जीवन.pdf | 130 |
| मीरा बाई का जीवन.pdf | 130 |
| ಭೀಷ್ಮ ಪಿತಾಮಹರ ಕಥೆ_.pdf | 126 |
| ಶಿಕ್ಷಪ್ರದ_.pdf | 126 |
| ಸಮಯದ ಸದುಪಯೋಗ ಹೇಗೆ_.pdf | 126 |
| ravan-samhita-2.pdf | 124 |
| Importance_Of_Riaz_In_Indian_Classical_Music.pdf | 124 |
| 001-Garg-Sanhita.pdf | 122 |
| Introduction-to-Vedanta-by-Swami-Dayananda.pdf | 120 |
| Gheranda Samhita.pdf | 117 |
| ravan-samhita-4.pdf | 115 |
| ebharati-pdf-1674278317DhanurvedaSamhita-Sam-1958.pdf | 114 |
| लक्ष्मी_प्राप्ति_के_दुर्लभ_प्रयोग.pdf | 111 |
| 107-Valmiki-Ramayan-Telugu.pdf | 109 |
| 2015.541564.Uddish-tantram.pdf | 109 |
| Chanakya Niti Darpan.pdf | 102 |
| 101-Valmiki-Ramayan-Telugu.pdf | 101 |
| 201-Valmiki-Ramayan-Telugu.pdf | 101 |
| Brahmacharya Ki Shakti by Swami Rama Tirtha.pdf | 100 |
| Yoga-rasayanam-sanskrit-hindi.pdf | 100 |
| 102-Valmiki-Ramayan-Telugu.pdf | 100 |
| 103-Valmiki-Ramayan-Telugu.pdf | 100 |
| 104-Valmiki-Ramayan-Telugu.pdf | 100 |
| 105-Valmiki-Ramayan-Telugu.pdf | 100 |
| 106-Valmiki-Ramayan-Telugu.pdf | 100 |
| 202-Valmiki-Ramayan-Telugu.pdf | 100 |
| 203-Valmiki-Ramayan-Telugu.pdf | 100 |
| Deskbook on Orthography of Devanagari Script (2)_compressed. | 98 |
| ವಾಸ್ತವಿಕ ಸುಖ ಆನಂದ_.pdf | 94 |
| shiva-swarodaya-sanskrit-hindi.pdf | 93 |
| mantra-vigyan.pdf | 81 |
| bhavanbhaskar-vastu-shastra (1).pdf | 80 |
| bhavanbhaskar-vastu-shastra.pdf | 80 |
| वैदिक गणित सूत्र.pdf | 79 |
| ವಿಷ್ಣು ಸಹಸ್ರ ನಾಮ_.pdf | 79 |
| Chakras.pdf | 77 |
| Siddha Rare Sadhanas (2).pdf | 71 |
| Paka Darpana of Nala Madhuri Hindi Commentary Indra Deva Tri | 69 |
| vishwa-ki-alokik-sadhnaye_compress.pdf | 68 |
| Strength+of+Brahmacharya.pdf | 67 |
| Gheranda Samhita_sanskrit_Eng.pdf | 64 |
| hanuman-bahuk-gitapress.pdf | 64 |
| ravan-samhita-1.pdf | 64 |
| Swarn Tantram.pdf | 64 |
| ಭಗವಂತನ ಕೃಪೆ_.pdf | 63 |
| panini_TheDhatupathaOfPanini.pdf | 56 |
| Ayurvedic Upay.pdf | 53 |
| VaisakhaPuranam-1.pdf | 49 |
| ravan-samhita-5.pdf | 48 |
| Shiva Sutra Spanda Karika (Samvat 2031 Edition) - Daita Swam | 48 |
| instaPDF.in-mandukya-upanishad-718.pdf | 44 |
| Copy of महात्मा विदुर.pdf | 43 |
| महात्मा विदुर.pdf | 43 |
| योग आसन ( चित्र ).pdf | 37 |
| महाभारत For Students.pdf | 36 |
| रामायण For Students.pdf | 36 |
| श्री कृष्ण लीला दर्शन.pdf | 35 |
| तुलसी के चमत्कारी गुण.pdf | 33 |
| Copy of नेताजी सुभाषचंद्र बोस.pdf | 25 |
| Copy of भगत सिंह.pdf | 25 |
| Copy of वीर सावरकर.pdf | 25 |
| नेताजी सुभाषचंद्र बोस.pdf | 25 |
| भगत सिंह.pdf | 25 |
| वीर सावरकर.pdf | 25 |
| Urvashi Sadhana.pdf | 25 |
| Copy of डॉ. हेडगेवार.pdf | 24 |
| Copy of पंडित_दीनदयाल_उपाध्याय.pdf | 24 |
| डॉ. हेडगेवार.pdf | 24 |
| पंडित_दीनदयाल_उपाध्याय.pdf | 24 |
| Copy of आर्यभट्ट.pdf | 21 |
| Copy of एकलव्य.pdf | 21 |
| Copy of कार्तिकेय.pdf | 21 |
| Copy of छत्रपति शिवाजी.pdf | 21 |
| Copy of जगद्गुरु शंकराचार्य.pdf | 21 |
| Copy of जीजाबाई.pdf | 21 |
| Copy of भक्त प्रहलाद.pdf | 21 |
| Copy of भगीरथ.pdf | 21 |
| Copy of महर्षि अगस्त्य.pdf | 21 |
| Copy of महर्षि वाल्मिकी.pdf | 21 |
| Copy of महर्षि वेदव्यास.pdf | 21 |
| Copy of महाराणा प्रताप.pdf | 21 |
| Copy of महासती द्रोपदी.pdf | 21 |
| Copy of मीराबाई.pdf | 21 |
| Copy of रानी लक्ष्मीबाई.pdf | 21 |
| Copy of वीर अभिमन्यु.pdf | 21 |
| Copy of श्री कृष्ण.pdf | 21 |
| Copy of श्री राम.pdf | 21 |
| Copy of सती सावित्री.pdf | 21 |
| आर्यभट्ट.pdf | 21 |
| एकलव्य.pdf | 21 |
| कार्तिकेय.pdf | 21 |
| छत्रपति शिवाजी.pdf | 21 |
| जगद्गुरु शंकराचार्य.pdf | 21 |
| जीजाबाई.pdf | 21 |
| भक्त प्रहलाद.pdf | 21 |
| भगीरथ.pdf | 21 |
| महर्षि अगस्त्य.pdf | 21 |
| महर्षि वाल्मिकी.pdf | 21 |
| महर्षि वेदव्यास.pdf | 21 |
| महाराणा प्रताप.pdf | 21 |
| महासती द्रोपदी.pdf | 21 |
| मीराबाई.pdf | 21 |
| रानी लक्ष्मीबाई.pdf | 21 |
| वीर अभिमन्यु.pdf | 21 |
| श्री कृष्ण.pdf | 21 |
| श्री राम.pdf | 21 |
| सती सावित्री.pdf | 21 |
| 2015.405980.Science-In.pdf | 21 |
| Copy of महर्षि विश्वामित्र.pdf | 20 |
| Copy of राजा राम मोहनराय.pdf | 20 |
| Copy of लव-कुश की वीरता.pdf | 20 |
| महर्षि विश्वामित्र.pdf | 20 |
| राजा राम मोहनराय.pdf | 20 |
| लव-कुश की वीरता.pdf | 20 |
| hanumanchalisa_Marwadi_Sanskrit.pdf | 19 |
| Padma-Puranam.pdf | 18 |
| Scanda-Puranam-Telugu.pdf | 18 |
| agni-puranam (1).pdf | 13 |
| Brahm Vaivart Puran 1.pdf | 6 |
| 60. Rashmi Yadav, Gwaliar (M.P.) .pdf | 5 |
| 08. Dr. Mohini Mehrotra.pdf | 4 |

---

## OCR Overlay Documents

**39 documents** have OCR overlay (scanned + invisible text):

| Document | Pages |
|----------|-------|
| 5_6334447321257870315.pdf | 1713 |
| Brahm Vaivart Puran 3.pdf | 888 |
| Garud Puran complete.pdf | 800 |
| Vishnu Puran Eng sans.pdf | 671 |
| Matasya Puran 2.pdf | 587 |
| Mahabharata-VOL-7.pdf | 585 |
| sabdakalpadrumah - 04.pdf | 584 |
| sabdakalpadrumah - 05 (1).pdf | 568 |
| Narad Panchatatra 2.pdf | 556 |
| BPHS - 2 RSanthanam.pdf | 552 |
| Mahabharata-VOL-4.pdf | 534 |
| Sushruta-Samhita.pdf | 534 |
| Vayu Puran 1.pdf | 507 |
| Mahabharata-VOL-6.pdf | 500 |
| BPHS - 1 RSanthanam.pdf | 482 |
| Vayu Puran 2.pdf | 478 |
| Nakshatras complete.pdf | 453 |
| Narad Puran 3.pdf | 444 |
| Narad Panchatatra 1.pdf | 432 |
| Narsimha Puran.pdf | 431 |
| Mahabharata-VOL-2.pdf | 426 |
| Mahabharata-VOL-3.pdf | 420 |
| Narad Puran 4.pdf | 420 |
| Mahabharata-VOL-9.pdf | 416 |
| Mahabharata-VOL-10.pdf | 415 |
| Mahabharata-VOL-8.pdf | 413 |
| Mahabharata-VOL-11.pdf | 409 |
| Varah puran 2.pdf | 397 |
| Varah puran 1.pdf | 380 |
| Kalki-Purana-english.pdf | 374 |
| Prashna Jyotish ( PDFDrive.com ).pdf | 331 |
| Brahmand Puran 4.pdf | 278 |
| Brahmand Puran 3.pdf | 248 |
| Brahmand Puran 5.pdf | 190 |
| Katha Upanishad Gita Press Gorakhpur.pdf | 182 |
| Kena Upanishad Gita Press Gorakhpur.pdf | 152 |
| yShiva Svarodaya Text With English Translation - Ram Kumar R | 104 |
| Shiva Svarodaya with Bhasha Tika by Pt. Mihira Chandra - Khe | 98 |
| 18. Theory of Ayurveda (Presentation) Author Dr Chakra Pany  | 35 |

---

## Hybrid Documents

**20 documents** contain both scanned and native pages:

| Document | Pages | Classes |
|----------|-------|---------|
| Harivamsha-Purana-Gitapress.pdf | 1421 | scanned_image:110, ocr_overlay:93 |
| Mandukya Upanishad - Gita Press Gorakhpur.pdf | 308 | scanned_image:84, blank:224 |
| TheKamaSutraofVatsyayana_11359535.pdf | 220 | scanned_image:52, ocr_overlay:7, native_text:136, blank:25 |
| kamasutraofvatsy00vatsuoft.pdf | 216 | scanned_image:50, ocr_overlay:166 |
| Katha Upanishad  - Gita Press Gorakhpur.pdf | 182 | scanned_image:129, blank:53 |
| Kena Upanishad - Gita Press Gorakhpur.pdf | 152 | scanned_image:114, blank:38 |
| brihaspatisutrao00brharich.pdf | 100 | scanned_image:48, ocr_overlay:52 |
| research-report-on-puran (2).pdf | 67 | native_text:53, scanned_image:13, blank:1 |
| 3. My Health My Responsibility Ayu Samvad Ayurveda | 44 | scanned_image:1, ocr_overlay:8, native_text:35 |
| 2015.378440.Aatm-Bodh_text.pdf | 36 | scanned_image:15, ocr_overlay:21 |
| 16. Introduction to Ayurveda (Presentation) Author | 23 | ocr_overlay:3, native_text:18, scanned_image:2 |
| Chakraca.pdf | 20 | scanned_image:8, ocr_overlay:9, native_text:3 |
| instapdf.in-karva-chauth-vrat-katha-299.pdf | 16 | scanned_image:6, ocr_overlay:10 |
| सूर्य-सूक्त-1.pdf | 16 | scanned_image:2, native_text:2, ocr_overlay:12 |
| -sankat-mochan-hanuman-ashtak-304 2.pdf | 15 | scanned_image:5, ocr_overlay:9, native_text:1 |
| Copy of आर्यभट्ट ( Hindi ).pdf | 8 | scanned_image:2, native_text:6 |
| आर्यभट्ट ( Hindi ).pdf | 8 | scanned_image:2, native_text:6 |
| विक्रम और बेताल.pdf | 8 | scanned_image:2, native_text:6 |
| Sankat Mochan Hanuman Ashtak  2.pdf | 3 | ocr_overlay:2, native_text:1 |
| 3-4-saama-vedamu.pdf | 2 | scanned_image:1, mixed_content:1 |

---

## Timed-Out Documents

**42 documents** exceeded the 60-second processing timeout:

| Document | Reason |
|----------|--------|
| Arthasastra Hindi Translation Udayvir Shastri.pdf | Timeout after 60s |
| aryabhata_with_english_commentary.pdf | Timeout after 60s |
| श्री_मद्भागवत_महापुराण_द्वितीय_खण्ड.pdf | Timeout after 60s |
| श्री_मद्भागवत_महापुराण_प्रथम_खण्ड.pdf | Timeout after 60s |
| bhrigu-samhita-hindi1.pdf | Timeout after 60s |
| gita-press-vedant-darshan-brahmasutra-sanskrit-hindi.pdf | Timeout after 60s |
| Swar vigyan.pdf | Timeout after 60s |
| durga-saptashati-hindi.pdf | Timeout after 60s |
| Vrddhayavanjataka of Minaraja 1.pdf | Timeout after 60s |
| bijak_kabir-_saheb.pdf | Timeout after 60s |
| charaksamhitaatridevajigupt-vol-2.pdf | Timeout after 60s |
| narayan-kwach.pdf | Timeout after 60s |
| suryaSiddhantaEnglish.pdf | Timeout after 60s |
| Mahabharata-VOL-1.pdf | Timeout after 60s |
| Mahabharata-VOL-5.pdf | Timeout after 60s |
| Mahabharata-VOL-I2.pdf | Timeout after 60s |
| panini_Ashtadhyayi_Book8.pdf | Timeout after 60s |
| panini_Ashtadhyayi_book3.pdf | Timeout after 60s |
| panini_Ashtadhyayi_book4.pdf | Timeout after 60s |
| panini_Ashtadhyayi_book6.pdf | Timeout after 60s |
| panini_Mahabhashya_II.pdf | Timeout after 60s |
| panini_Mahabhashya_VI.pdf | Timeout after 60s |
| kalkipuranhindi1.pdf | Timeout after 60s |
| ऋग्वेद.pdf | Timeout after 60s |
| MarkandeyaPuranamu.pdf | Timeout after 60s |
| bhavishyapuranam-telugu.pdf | Timeout after 60s |
| Brahmand Puran 1.pdf | Timeout after 60s |
| Brahmand Puran 2.pdf | Timeout after 60s |
| Kurm Puran.pdf | Timeout after 60s |
| Ling Puran 2.pdf | Timeout after 60s |
| Ling Puran Sans Eng 2.pdf | Timeout after 60s |
| Matasya Puran 1.pdf | Timeout after 60s |
| Shiv Puran 3.pdf | Timeout after 60s |
| Skand puran 3.pdf | Timeout after 60s |
| Skand puran 7.pdf | Timeout after 60s |
| Skand puran 8.pdf | Timeout after 60s |
| science-in-vedas.pdf | Timeout after 60s |
| 108 Upanishad Part-3.pdf | Timeout after 60s |
| vimanika shaster.pdf | Timeout after 60s |
| Sri_Shankaracharya-AtmaBodha (and Other Stotras) - Swami Nik | Timeout after 60s |
| 2015.464310.Dynamic-Astrology.pdf | Timeout after 60s |
| Valmiki Ramayanam Baalakanda- N Ranganatha sharma.pdf | Timeout after 60s |

---

## Why the Phase 3 Classifier Was Wrong

The Phase 3 classifier used `page.get_text()` as its primary signal.
This approach has a critical flaw:

1. **OCR-overlaid scans** contain both a scanned image AND invisible OCR text
2. `page.get_text()` extracts the invisible OCR text successfully
3. The classifier sees 'text exists' and concludes 'native text'
4. **Result: Scanned pages with OCR overlays are misclassified as native**

The multi-signal classifier corrects this by measuring:
- Image coverage percentage (scans have >80% image coverage)
- DPI estimation (scans have >150 DPI images)
- Text/image bounding box overlap
- Font type analysis (OCR text uses CID fonts with uniform sizes)

---

## Production Pipeline Implications

The production document processing pipeline **must** include:

1. **Document classifier** — Uses multi-signal analysis, not just text extraction
2. **OCR router** — Routes scanned/OCR-overlay pages to Tesseract/PaddleOCR
3. **Hybrid processor** — Handles documents with mixed native and scanned pages
4. **Quality validation** — Validates extraction quality before knowledge lake ingestion

PyMuPDF alone is **insufficient** for the full corpus.

---

*Report generated: 2026-07-11 21:42 UTC*
*Processing time: 3584s*