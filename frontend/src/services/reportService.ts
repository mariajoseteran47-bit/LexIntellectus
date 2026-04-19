import api from '@/lib/api';

export interface ReportKPIs {
    active_cases: number;
    new_cases_period: number;
    closed_cases_period: number;
    pending_deadlines: number;
    urgent_deadlines: number;
    overdue_deadlines: number;
    resolution_rate: number;
    docs_period: number;
    active_clients: number;
    total_cases: number;
}

export interface CaseByRamo {
    name: string;
    count: number;
    pct: number;
}

export interface StatusDistribution {
    label: string;
    count: number;
    color_hex: string | null;
    es_final: boolean;
    pct: number;
}

export interface MonthlyActivity {
    month: string;
    year: number;
    cases: number;
    deadlines: number;
}

export interface PriorityDistribution {
    priority: string;
    count: number;
}

export interface TopLawyer {
    nombre: string;
    case_count: number;
}

export interface ReportOverview {
    period: string;
    date_range: { start: string; end: string };
    kpis: ReportKPIs;
    cases_by_ramo: CaseByRamo[];
    status_distribution: StatusDistribution[];
    monthly_activity: MonthlyActivity[];
    priority_distribution: PriorityDistribution[];
    top_lawyers: TopLawyer[];
}

export const reportService = {
    async getOverview(period: string = 'month'): Promise<ReportOverview> {
        const { data } = await api.get<ReportOverview>('/reports/overview', {
            params: { period }
        });
        return data;
    },
};
