export interface NavItem {
  title: string;
  item?: Item;
  items?: NavItem[];
}

interface Item {
  href: string;
  iconName: string;
  extraPath?: string[];
  exactPath?: boolean;
  badge?: number;
}
