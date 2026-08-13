"""
Solana Devnet Signer & Transaction Broadcaster.
Handles keypair signing in non-custodial code isolation.
"""
import uuid
from datetime import datetime, timezone
from solders.keypair import Keypair
from solana_agent.config import solana_settings
from solana_agent.schemas import ExecutionResult


class SolanaDevnetClient:
    def __init__(self):
        self._keypair = self._load_or_generate_keypair()

    def _load_or_generate_keypair(self) -> Keypair:
        pk_str = solana_settings.solana_private_key.strip()
        if pk_str:
            try:
                # If valid base58 or byte list provided
                if "[" in pk_str and "]" in pk_str:
                    import json
                    byte_list = json.loads(pk_str)
                    return Keypair.from_bytes(bytes(byte_list))
                return Keypair.from_base58_string(pk_str)
            except Exception:
                pass
        # Fallback to isolated transient keypair for Devnet testing
        return Keypair()

    @property
    def public_key_str(self) -> str:
        return str(self._keypair.pubkey())

    async def execute_devnet_transaction(self, sol_amount: float, memo_text: str) -> ExecutionResult:
        """
        Signs and broadcasts Devnet transaction to Solana Devnet RPC.
        Fails closed on any error or missing balance.
        """
        from solana.rpc.async_api import AsyncClient
        from solders.instruction import Instruction, AccountMeta
        from solders.pubkey import Pubkey
        from solders.message import MessageV0
        from solders.transaction import VersionedTransaction

        client = AsyncClient(solana_settings.solana_rpc_url)
        try:
            bal_res = await client.get_balance(self._keypair.pubkey())
            bal = bal_res.value if bal_res else 0

            if bal <= 0:
                await client.close()
                return ExecutionResult(
                    status="PENDING_DEVNET_AIRDROP",
                    cluster="devnet",
                    tx_signature=None,
                    timestamp_utc=datetime.now(timezone.utc).isoformat(),
                )

            # Build and sign real Devnet transaction
            memo_program_id = Pubkey.from_string("MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr")
            memo_ix = Instruction(
                memo_program_id,
                memo_text.encode("utf-8"),
                [AccountMeta(self._keypair.pubkey(), is_signer=True, is_writable=True)]
            )
            bh_res = await client.get_latest_blockhash()
            msg = MessageV0.try_compile(self._keypair.pubkey(), [memo_ix], [], bh_res.value.blockhash)
            tx = VersionedTransaction(msg, [self._keypair])

            send_res = await client.send_transaction(tx)
            await client.close()

            real_sig = str(send_res.value)
            return ExecutionResult(
                status="EXECUTED",
                cluster="devnet",
                tx_signature=real_sig,
                timestamp_utc=datetime.now(timezone.utc).isoformat(),
            )
        except Exception as e:
            try:
                await client.close()
            except Exception:
                pass
            return ExecutionResult(
                status="FAILED",
                cluster="devnet",
                tx_signature=None,
                timestamp_utc=datetime.now(timezone.utc).isoformat(),
            )


solana_client = SolanaDevnetClient()
