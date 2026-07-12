/* FR → EN for keywords/niches shown in the UI. Curated against the actual roster vocabulary
   (198 unique keywords at last count). Unknown terms pass through untranslated — never guessed. */
(() => {
  const FR_EN = {
    "friperie": "thrift shop", "fripe": "thrift", "100% fripe": "100% thrift",
    "friperie en ligne": "online thrift shop", "friperie en gros": "wholesale thrift",
    "fripe en gros": "wholesale thrift", "grossiste friperie": "thrift wholesaler",
    "chaussures friperie": "thrift shoes", "friperie premier choix": "grade-A thrift",
    "grossiste": "wholesaler", "grossistes": "wholesalers",
    "vente en gros": "wholesale", "pack de gros": "bulk pack", "en gros": "wholesale",
    "fournisseur": "supplier", "fournisseurs": "suppliers",
    "sourcing fournisseurs": "supplier sourcing", "destockage": "clearance stock",
    "revente": "resale", "achat revente": "buy-to-resell", "achat-revente": "buy-to-resell",
    "achat revente vinted": "Vinted flipping", "revendeur": "reseller",
    "vendre vite": "sell fast", "vente rapide": "quick sale",
    "optimisation ventes": "sales optimisation", "astuces vente": "selling tips",
    "seconde main": "secondhand", "secondemain": "secondhand",
    "vetements seconde main": "secondhand clothing", "premier choix": "grade A",
    "ballot vintage": "vintage bale", "balle": "bale", "ballot": "bale",
    "brocante": "flea market", "depot-vente": "consignment", "depot vente": "consignment",
    "depot chine": "China depot", "videdressing": "closet sale", "vide dressing": "closet sale",
    "vente live": "live selling", "ventelive": "live selling", "liveshopping": "live shopping",
    "facebook lives": "Facebook lives", "commandes whatsapp": "WhatsApp orders",
    "pascher": "cheap finds", "pas cher": "cheap", "bonplan": "good deal", "bon plan": "good deal",
    "petit prix": "low prices", "mercredifrip": "thrift wednesdays",
    "mode femme homme": "men's & women's fashion", "mode": "fashion",
    "vente ensembles femme": "women's sets", "montres": "watches", "sacs": "bags",
    "parfum": "fragrance", "accessoires": "accessories", "neuves": "brand new",
    "entretien": "care & upkeep", "livraison": "delivery", "formation": "training course",
    "reseller formation": "reseller training", "dressing": "wardrobe",
    "bien-être famille": "family wellbeing", "ados": "teens", "girly": "girly",
    "outfit": "outfit", "multi-magasins": "multi-store", "microstore": "micro-store",
    "vinted": "Vinted", "business vinted": "Vinted business", "vinted business": "Vinted business",
    "vinted bot": "Vinted bot", "vinted selling": "Vinted selling",
    "revente vinted": "Vinted flipping", "vinted tips": "Vinted tips",
    "flipping stock": "stock flipping", "vintage": "vintage", "streetwear": "streetwear",
    "montpellier": "Montpellier", "paris": "Paris",
    "friperiemontpellier": "Montpellier thrift", "sourcing": "sourcing",
    "agents": "agents", "packs": "bundles", "vlog": "vlog",
    "vetements homme": "menswear", "vetements": "clothing",
  };
  window.Lang = {
    mode: "original",
    toggle() { this.mode = this.mode === "original" ? "en" : "original"; },
    t(term) {
      if (this.mode === "original") return term;
      return FR_EN[String(term).toLowerCase().trim()] || term;
    },
  };
})();
