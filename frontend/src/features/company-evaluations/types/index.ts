export interface EvaluationPayload {
    score: number; // 0 - 10
    evaluation: string;
    recommendation: 'HIRE_FTE' | 'PART_TIME' | 'COMPLETED';
}