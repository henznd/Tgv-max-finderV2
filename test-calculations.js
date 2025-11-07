// Test des calculs d'arbitrage
// Exécuter avec : node test-calculations.js

function calculateArbitrage(input) {
    const { victoryOdds, drawOdds, defeatOdds, freebetAmount, cashAmount } = input;

    // Validation
    if (victoryOdds <= 1 || drawOdds <= 1 || defeatOdds <= 1) {
        return { error: "Toutes les cotes doivent être supérieures à 1" };
    }

    if (freebetAmount < 0 || cashAmount < 0) {
        return { error: "Les montants ne peuvent pas être négatifs" };
    }

    // Vérification de l'arbitrage possible
    const sum = (1 / victoryOdds) + (1 / drawOdds) + (1 / defeatOdds);
    if (sum >= 1) {
        return { error: "Ces cotes ne permettent pas d'arbitrage (somme des inverses ≥ 1)" };
    }

    // Calcul pour les freebets
    const freebetGain = freebetAmount / (
        (1 / (victoryOdds - 1)) + 
        (1 / (drawOdds - 1)) + 
        (1 / (defeatOdds - 1))
    );

    const freebetDistribution = {
        victory: freebetGain / (victoryOdds - 1),
        draw: freebetGain / (drawOdds - 1),
        defeat: freebetGain / (defeatOdds - 1)
    };

    // Calcul pour le cash
    const cashGain = cashAmount / (
        (1 / victoryOdds) + 
        (1 / drawOdds) + 
        (1 / defeatOdds)
    );

    const cashDistribution = {
        victory: cashGain / victoryOdds,
        draw: cashGain / drawOdds,
        defeat: cashGain / defeatOdds
    };

    // Gain garanti total
    const guaranteedProfit = freebetGain + cashGain;
    const totalInvestment = cashAmount;
    const roi = ((guaranteedProfit - totalInvestment) / totalInvestment) * 100;

    return {
        freebetDistribution,
        cashDistribution,
        guaranteedProfit,
        totalInvestment,
        roi
    };
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('fr-FR', {
        style: 'currency',
        currency: 'EUR',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(amount);
}

// Tests
console.log("🧮 Tests des calculs d'arbitrage\n");

// Test 1: Cas de base
console.log("📊 Test 1: Cas de base");
const test1 = calculateArbitrage({
    victoryOdds: 2.5,
    drawOdds: 3.2,
    defeatOdds: 2.8,
    freebetAmount: 100,
    cashAmount: 100
});

if (test1.error) {
    console.log("❌ Erreur:", test1.error);
} else {
    console.log("✅ Gain garanti:", formatCurrency(test1.guaranteedProfit));
    console.log("💰 Investissement:", formatCurrency(test1.totalInvestment));
    console.log("📈 ROI:", test1.roi.toFixed(2) + "%");
    console.log("🎁 Freebets - Victoire:", formatCurrency(test1.freebetDistribution.victory));
    console.log("💶 Cash - Victoire:", formatCurrency(test1.cashDistribution.victory));
}

console.log("\n" + "=".repeat(50) + "\n");

// Test 2: Cotes très favorables
console.log("📊 Test 2: Cotes très favorables");
const test2 = calculateArbitrage({
    victoryOdds: 1.5,
    drawOdds: 4.0,
    defeatOdds: 6.0,
    freebetAmount: 50,
    cashAmount: 200
});

if (test2.error) {
    console.log("❌ Erreur:", test2.error);
} else {
    console.log("✅ Gain garanti:", formatCurrency(test2.guaranteedProfit));
    console.log("💰 Investissement:", formatCurrency(test2.totalInvestment));
    console.log("📈 ROI:", test2.roi.toFixed(2) + "%");
}

console.log("\n" + "=".repeat(50) + "\n");

// Test 3: Cas impossible (somme des inverses >= 1)
console.log("📊 Test 3: Cas impossible");
const test3 = calculateArbitrage({
    victoryOdds: 1.1,
    drawOdds: 1.1,
    defeatOdds: 1.1,
    freebetAmount: 100,
    cashAmount: 100
});

if (test3.error) {
    console.log("❌ Erreur:", test3.error);
} else {
    console.log("✅ Gain garanti:", formatCurrency(test3.guaranteedProfit));
}

console.log("\n" + "=".repeat(50) + "\n");

// Test 4: Vérification des gains égaux
console.log("📊 Test 4: Vérification des gains égaux");
const test4 = calculateArbitrage({
    victoryOdds: 2.0,
    drawOdds: 3.0,
    defeatOdds: 4.0,
    freebetAmount: 60,
    cashAmount: 120
});

if (test4.error) {
    console.log("❌ Erreur:", test4.error);
} else {
    // Calcul des gains pour chaque issue
    const gainVictory = test4.freebetDistribution.victory * (2.0 - 1) + test4.cashDistribution.victory * 2.0;
    const gainDraw = test4.freebetDistribution.draw * (3.0 - 1) + test4.cashDistribution.draw * 3.0;
    const gainDefeat = test4.freebetDistribution.defeat * (4.0 - 1) + test4.cashDistribution.defeat * 4.0;
    
    console.log("✅ Gain garanti:", formatCurrency(test4.guaranteedProfit));
    console.log("🎯 Gain si victoire:", formatCurrency(gainVictory));
    console.log("🎯 Gain si nul:", formatCurrency(gainDraw));
    console.log("🎯 Gain si défaite:", formatCurrency(gainDefeat));
    
    const tolerance = 0.01; // Tolérance de 1 centime
    const gainsEqual = Math.abs(gainVictory - gainDraw) < tolerance && 
                      Math.abs(gainDraw - gainDefeat) < tolerance &&
                      Math.abs(gainVictory - test4.guaranteedProfit) < tolerance;
    
    console.log(gainsEqual ? "✅ Gains égaux confirmés" : "❌ Gains inégaux");
}

console.log("\n🎯 Tests terminés !"); 