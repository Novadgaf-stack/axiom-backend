"""
Solana Agent Layer Configuration.
Strictly defaults to Solana Devnet and enforces safety boundaries.
"""
import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class SolanaSettings:
    solana_rpc_url: str = field(
        default_factory=lambda: os.getenv("SOLANA_DEVNET_RPC_URL", "https://api.devnet.solana.com")
    )
    solana_private_key: str = field(
        default_factory=lambda: os.getenv("SOLANA_DEVNET_PRIVATE_KEY", "")
    )
    solana_cluster: str = field(
        default_factory=lambda: os.getenv("SOLANA_CLUSTER", "devnet").lower()
    )
    max_sol_per_tx: float = field(
        default_factory=lambda: float(os.getenv("SOLANA_MAX_SOL_PER_TX", "0.1"))
    )
    max_tx_per_hour: int = field(
        default_factory=lambda: int(os.getenv("SOLANA_MAX_TX_PER_HOUR", "5"))
    )
    min_confidence_floor: int = field(
        default_factory=lambda: int(os.getenv("SOLANA_MIN_CONFIDENCE", "85"))
    )

    def validate(self) -> list[str]:
        problems = []
        if "mainnet" in self.solana_rpc_url.lower() or self.solana_cluster == "mainnet":
            problems.append("FORBIDDEN: Mainnet Solana cluster requested. Nexus-7 Solana layer is DEVNET ONLY.")
        if self.max_sol_per_tx > 1.0:
            problems.append("FORBIDDEN: max_sol_per_tx exceeds Devnet safety limit of 1.0 SOL.")
        return problems


solana_settings = SolanaSettings()
