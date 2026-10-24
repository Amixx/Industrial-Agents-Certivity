export type Source = { regulation: string; version: string; page: number; paragraph?: string };

export type Requirement = { id: string; text: string; source: Source };

export type Regulation = {
	regulation: string;
	title: string;
	versions: { role: string; version_label: string; status: string; files: { name: string }[] }[];
};

export type RequirementsResult = { team_id: string; case_id: string; requirements: Requirement[] };

export type RegulationGroup = {
	regulation: string;
	title: string;
	count: number;
	requirements: Requirement[];
};
