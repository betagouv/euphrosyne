export interface NavItem {
  title: string;
  href: string;
  iconName: string;
  extraPath?: string[];
  exactPath?: boolean;
  badge?: number;
}
