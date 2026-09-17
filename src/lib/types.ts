export type CampusSlug =
  | "ann-arbor"
  | "cambridge"
  | "palo-alto"
  | "berkeley"
  | "pittsburgh"
  | "austin";

export type Campus = {
  slug: CampusSlug;
  index: string; // e.g. "01"
  name: string; // "University of Michigan"
  shortName: string; // "UMich EECS / Beyster"
  city: string;
  coordinates: string; // "42.28°N"
  dispatch: string; // "24H DISPATCH"
  students: number;
  inventoryPct: number;
  ambassador: string;
  labs: string[];
};

export type ProductBadge = "FLAGSHIP" | "POPULAR" | "RESTOCKED" | "LIMITED" | "NEW";

export type Product = {
  slug: string;
  sku: string;
  name: string;
  category: string; // "DRY-FIT COMPONENT"
  price: number;
  colorway: string;
  description: string;
  fabricSpec: string;
  badge?: ProductBadge;
  campus: CampusSlug | "all";
  sizes: string[];
  gsm: number;
  tone: "light" | "dark"; // controls placeholder art treatment
};

export type CartLine = {
  slug: string;
  size: string;
  quantity: number;
};
