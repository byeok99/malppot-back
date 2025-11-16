export const TIER_CONFIG = {
    FOREST: { name: "숲", icon: "🏞️", streak: 30, count: 150 },
    TREE: { name: "나무", icon: "🌳", streak: 15, count: 50 },
    SPROUT: { name: "새싹", icon: "🌿", streak: 3, count: 10 },
    SEED: { name: "씨앗", icon: "🌱", streak: 1, count: 1 },
};

export const getTier = (streak: number, count: number) => {
    if (streak >= TIER_CONFIG.FOREST.streak && count >= TIER_CONFIG.FOREST.count) return TIER_CONFIG.FOREST;
    if (streak >= TIER_CONFIG.TREE.streak && count >= TIER_CONFIG.TREE.count) return TIER_CONFIG.TREE;
    if (streak >= TIER_CONFIG.SPROUT.streak && count >= TIER_CONFIG.SPROUT.count) return TIER_CONFIG.SPROUT;
    if (streak >= TIER_CONFIG.SEED.streak || count >= TIER_CONFIG.SEED.count) return TIER_CONFIG.SEED;
    return TIER_CONFIG.SEED;
};

// 티어별 기준 설명 문자열 생성
export const getTierDescription = (tier: any) => {
    return `${tier.icon} ${tier.name}: 연속 ${tier.streak}일 & 총 ${tier.count}회 이상 연습 시 달성`;
}
