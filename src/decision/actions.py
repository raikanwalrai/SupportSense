"""
SupportSense decision and action registry.

The ML model predicts an intent.
This module maps that intent to a safe, simulated operational action.

No real customer-impacting action is executed here.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ActionDefinition:
    intent: str
    action_id: str
    action_name: str
    risk: str
    requires_approval: bool
    simulation_message: str


def get_action(intent: str) -> ActionDefinition:
    """
    Return the operational action associated with an ML intent.

    Sprint 7 actions are simulation-only.
    """

    try:
        return ACTION_REGISTRY[intent]
    except KeyError as exc:
        raise ValueError(
            f"No action is registered for intent: {intent}"
        ) from exc


def _action(
    intent: str,
    action_id: str,
    action_name: str,
    risk: str = "LOW",
    requires_approval: bool = False,
    simulation_message: str | None = None,
) -> ActionDefinition:
    """Create a consistent simulated action definition."""

    if simulation_message is None:
        simulation_message = (
            f"{action_name} workflow simulated successfully."
        )

    return ActionDefinition(
        intent=intent,
        action_id=action_id,
        action_name=action_name,
        risk=risk,
        requires_approval=requires_approval,
        simulation_message=simulation_message,
    )


# ============================================================
# SUPPORTSENSE INTENT → ACTION REGISTRY
# ============================================================
#
# All actions are simulation-only in Sprint 7.
#
# LOW:
#     Informational or diagnostic actions.
#
# MEDIUM:
#     Customer workflow that would normally require controlled
#     execution.
#
# HIGH:
#     Sensitive customer/account/security operations requiring
#     human approval.
#
# ============================================================

ACTION_REGISTRY: dict[str, ActionDefinition] = {

    # --------------------------------------------------------
    # ACCOUNT / IDENTITY
    # --------------------------------------------------------

    "age_limit": _action(
        "age_limit",
        "CHECK_AGE_REQUIREMENTS",
        "Check age requirements",
    ),

    "country_support": _action(
        "country_support",
        "CHECK_COUNTRY_SUPPORT",
        "Check supported country",
    ),

    "edit_personal_details": _action(
        "edit_personal_details",
        "UPDATE_PERSONAL_DETAILS",
        "Update personal details",
        risk="MEDIUM",
    ),

    "passcode_forgotten": _action(
        "passcode_forgotten",
        "RESET_PASSCODE",
        "Reset passcode",
        risk="MEDIUM",
    ),

    "lost_or_stolen_phone": _action(
        "lost_or_stolen_phone",
        "SECURE_LOST_OR_STOLEN_PHONE",
        "Secure lost or stolen phone",
        risk="HIGH",
        requires_approval=True,
        simulation_message=(
            "Lost or stolen phone security workflow requires "
            "human approval."
        ),
    ),

    "terminate_account": _action(
        "terminate_account",
        "TERMINATE_ACCOUNT",
        "Terminate account",
        risk="HIGH",
        requires_approval=True,
        simulation_message=(
            "Account termination requires human approval."
        ),
    ),

    "unable_to_verify_identity": _action(
        "unable_to_verify_identity",
        "INVESTIGATE_IDENTITY_VERIFICATION",
        "Investigate identity verification",
        risk="MEDIUM",
    ),

    "verify_my_identity": _action(
        "verify_my_identity",
        "START_IDENTITY_VERIFICATION",
        "Start identity verification",
        risk="MEDIUM",
    ),

    "verify_source_of_funds": _action(
        "verify_source_of_funds",
        "VERIFY_SOURCE_OF_FUNDS",
        "Verify source of funds",
        risk="MEDIUM",
    ),

    "why_verify_identity": _action(
        "why_verify_identity",
        "EXPLAIN_IDENTITY_VERIFICATION",
        "Explain identity verification",
    ),

    # --------------------------------------------------------
    # CARDS
    # --------------------------------------------------------

    "activate_my_card": _action(
        "activate_my_card",
        "ACTIVATE_CARD",
        "Activate card",
        risk="MEDIUM",
    ),

    "apple_pay_or_google_pay": _action(
        "apple_pay_or_google_pay",
        "SETUP_MOBILE_WALLET",
        "Set up Apple Pay or Google Pay",
        risk="MEDIUM",
    ),

    "card_about_to_expire": _action(
        "card_about_to_expire",
        "REPLACE_EXPIRING_CARD",
        "Replace expiring card",
        risk="MEDIUM",
    ),

    "card_acceptance": _action(
        "card_acceptance",
        "CHECK_CARD_ACCEPTANCE",
        "Check card acceptance",
    ),

    "card_arrival": _action(
        "card_arrival",
        "CHECK_CARD_DELIVERY",
        "Check card delivery status",
    ),

    "card_delivery_estimate": _action(
        "card_delivery_estimate",
        "ESTIMATE_CARD_DELIVERY",
        "Estimate card delivery",
    ),

    "card_linking": _action(
        "card_linking",
        "LINK_CARD",
        "Link card",
        risk="MEDIUM",
    ),

    "card_not_working": _action(
        "card_not_working",
        "TROUBLESHOOT_CARD",
        "Troubleshoot card",
    ),

    "card_swallowed": _action(
        "card_swallowed",
        "HANDLE_RETAINED_CARD",
        "Handle retained card",
        risk="MEDIUM",
    ),

    "compromised_card": _action(
        "compromised_card",
        "SECURE_COMPROMISED_CARD",
        "Secure compromised card",
        risk="HIGH",
        requires_approval=True,
        simulation_message=(
            "Compromised-card security workflow requires "
            "human approval."
        ),
    ),

    "contactless_not_working": _action(
        "contactless_not_working",
        "TROUBLESHOOT_CONTACTLESS",
        "Troubleshoot contactless payments",
    ),

    "get_physical_card": _action(
        "get_physical_card",
        "ORDER_PHYSICAL_CARD",
        "Order physical card",
        risk="MEDIUM",
    ),

    "getting_spare_card": _action(
        "getting_spare_card",
        "ORDER_SPARE_CARD",
        "Order spare card",
        risk="MEDIUM",
    ),

    "getting_virtual_card": _action(
        "getting_virtual_card",
        "CREATE_VIRTUAL_CARD",
        "Create virtual card",
        risk="MEDIUM",
    ),

    "get_disposable_virtual_card": _action(
        "get_disposable_virtual_card",
        "CREATE_DISPOSABLE_VIRTUAL_CARD",
        "Create disposable virtual card",
        risk="MEDIUM",
    ),

    "disposable_card_limits": _action(
        "disposable_card_limits",
        "CHECK_DISPOSABLE_CARD_LIMITS",
        "Check disposable card limits",
    ),

    "lost_or_stolen_card": _action(
        "lost_or_stolen_card",
        "SECURE_LOST_OR_STOLEN_CARD",
        "Secure lost or stolen card",
        risk="HIGH",
        requires_approval=True,
        simulation_message=(
            "Lost or stolen card security workflow requires "
            "human approval."
        ),
    ),

    "order_physical_card": _action(
        "order_physical_card",
        "ORDER_PHYSICAL_CARD",
        "Order physical card",
        risk="MEDIUM",
    ),

    "pin_blocked": _action(
        "pin_blocked",
        "UNBLOCK_PIN",
        "Unblock PIN",
        risk="MEDIUM",
    ),

    "change_pin": _action(
        "change_pin",
        "CHANGE_PIN",
        "Change PIN",
        risk="MEDIUM",
    ),

    "supported_cards_and_currencies": _action(
        "supported_cards_and_currencies",
        "CHECK_SUPPORTED_CARDS",
        "Check supported cards and currencies",
    ),

    "visa_or_mastercard": _action(
        "visa_or_mastercard",
        "CHECK_CARD_NETWORK",
        "Check Visa or Mastercard availability",
    ),

    "virtual_card_not_working": _action(
        "virtual_card_not_working",
        "TROUBLESHOOT_VIRTUAL_CARD",
        "Troubleshoot virtual card",
    ),

    # --------------------------------------------------------
    # CARD PAYMENTS
    # --------------------------------------------------------

    "card_payment_fee_charged": _action(
        "card_payment_fee_charged",
        "INVESTIGATE_CARD_PAYMENT_FEE",
        "Investigate card payment fee",
        risk="MEDIUM",
    ),

    "card_payment_not_recognised": _action(
        "card_payment_not_recognised",
        "INVESTIGATE_CARD_PAYMENT",
        "Investigate unrecognised card payment",
        risk="HIGH",
        requires_approval=True,
    ),

    "direct_debit_payment_not_recognised": _action(
        "direct_debit_payment_not_recognised",
        "INVESTIGATE_DIRECT_DEBIT",
        "Investigate unrecognised direct debit",
        risk="HIGH",
        requires_approval=True,
        simulation_message=(
            "Unrecognised direct debit investigation requires "
            "human approval."
        ),
    ),

    "card_payment_wrong_exchange_rate": _action(
        "card_payment_wrong_exchange_rate",
        "INVESTIGATE_CARD_EXCHANGE_RATE",
        "Investigate card payment exchange rate",
        risk="MEDIUM",
    ),

    "declined_card_payment": _action(
        "declined_card_payment",
        "INVESTIGATE_DECLINED_CARD_PAYMENT",
        "Investigate declined card payment",
    ),

    "extra_charge_on_statement": _action(
        "extra_charge_on_statement",
        "INVESTIGATE_EXTRA_CHARGE",
        "Investigate extra statement charge",
        risk="MEDIUM",
    ),

    "pending_card_payment": _action(
        "pending_card_payment",
        "CHECK_PENDING_CARD_PAYMENT",
        "Check pending card payment",
    ),

    "reverted_card_payment?": _action(
        "reverted_card_payment?",
        "CHECK_REVERTED_CARD_PAYMENT",
        "Check reverted card payment",
    ),

    "transaction_charged_twice": _action(
        "transaction_charged_twice",
        "INVESTIGATE_DUPLICATE_CHARGE",
        "Investigate duplicate charge",
        risk="MEDIUM",
    ),

    # --------------------------------------------------------
    # CASH WITHDRAWALS / ATM
    # --------------------------------------------------------

    "atm_support": _action(
        "atm_support",
        "CHECK_ATM_SUPPORT",
        "Check ATM support",
    ),

    "cash_withdrawal_charge": _action(
        "cash_withdrawal_charge",
        "INVESTIGATE_CASH_WITHDRAWAL_FEE",
        "Investigate cash withdrawal fee",
        risk="MEDIUM",
    ),

    "cash_withdrawal_not_recognised": _action(
        "cash_withdrawal_not_recognised",
        "INVESTIGATE_CASH_WITHDRAWAL",
        "Investigate unrecognised cash withdrawal",
        risk="HIGH",
        requires_approval=True,
    ),

    "declined_cash_withdrawal": _action(
        "declined_cash_withdrawal",
        "INVESTIGATE_DECLINED_CASH_WITHDRAWAL",
        "Investigate declined cash withdrawal",
    ),

    "pending_cash_withdrawal": _action(
        "pending_cash_withdrawal",
        "CHECK_PENDING_CASH_WITHDRAWAL",
        "Check pending cash withdrawal",
    ),

    "wrong_amount_of_cash_received": _action(
        "wrong_amount_of_cash_received",
        "INVESTIGATE_CASH_AMOUNT",
        "Investigate incorrect cash amount",
        risk="MEDIUM",
    ),

    "wrong_exchange_rate_for_cash_withdrawal": _action(
        "wrong_exchange_rate_for_cash_withdrawal",
        "INVESTIGATE_CASH_EXCHANGE_RATE",
        "Investigate cash withdrawal exchange rate",
        risk="MEDIUM",
    ),

    # --------------------------------------------------------
    # TRANSFERS
    # --------------------------------------------------------

    "balance_not_updated_after_bank_transfer": _action(
        "balance_not_updated_after_bank_transfer",
        "INVESTIGATE_BANK_TRANSFER_BALANCE",
        "Investigate bank transfer balance",
        risk="MEDIUM",
    ),

    "beneficiary_not_allowed": _action(
        "beneficiary_not_allowed",
        "INVESTIGATE_BENEFICIARY",
        "Investigate beneficiary restriction",
        risk="MEDIUM",
    ),

    "cancel_transfer": _action(
        "cancel_transfer",
        "CANCEL_TRANSFER",
        "Cancel transfer",
        risk="MEDIUM",
    ),

    "declined_transfer": _action(
        "declined_transfer",
        "INVESTIGATE_DECLINED_TRANSFER",
        "Investigate declined transfer",
        risk="MEDIUM",
    ),

    "failed_transfer": _action(
        "failed_transfer",
        "INVESTIGATE_FAILED_TRANSFER",
        "Investigate failed transfer",
        risk="MEDIUM",
    ),

    "pending_transfer": _action(
        "pending_transfer",
        "CHECK_PENDING_TRANSFER",
        "Check pending transfer",
    ),

    "receiving_money": _action(
        "receiving_money",
        "CHECK_RECEIVING_MONEY",
        "Check receiving money",
    ),

    "transfer_fee_charged": _action(
        "transfer_fee_charged",
        "INVESTIGATE_TRANSFER_FEE",
        "Investigate transfer fee",
        risk="MEDIUM",
    ),

    "transfer_into_account": _action(
        "transfer_into_account",
        "TRANSFER_INTO_ACCOUNT",
        "Transfer money into account",
        risk="MEDIUM",
    ),

    "transfer_not_received_by_recipient": _action(
        "transfer_not_received_by_recipient",
        "INVESTIGATE_TRANSFER_RECIPIENT",
        "Investigate transfer not received",
        risk="MEDIUM",
    ),

    "transfer_timing": _action(
        "transfer_timing",
        "CHECK_TRANSFER_TIMING",
        "Check transfer timing",
    ),

    # --------------------------------------------------------
    # REFUNDS
    # --------------------------------------------------------

    "Refund_not_showing_up": _action(
        "Refund_not_showing_up",
        "CHECK_REFUND_STATUS",
        "Check refund status",
    ),

    "request_refund": _action(
        "request_refund",
        "REQUEST_REFUND",
        "Request refund",
        risk="MEDIUM",
    ),

    # --------------------------------------------------------
    # TOP UPS
    # --------------------------------------------------------

    "automatic_top_up": _action(
        "automatic_top_up",
        "MANAGE_AUTOMATIC_TOP_UP",
        "Manage automatic top up",
        risk="MEDIUM",
    ),

    "pending_top_up": _action(
        "pending_top_up",
        "CHECK_PENDING_TOP_UP",
        "Check pending top up",
    ),

    "top_up_by_bank_transfer_charge": _action(
        "top_up_by_bank_transfer_charge",
        "INVESTIGATE_BANK_TOP_UP_FEE",
        "Investigate bank transfer top up fee",
        risk="MEDIUM",
    ),

    "top_up_by_card_charge": _action(
        "top_up_by_card_charge",
        "INVESTIGATE_CARD_TOP_UP_FEE",
        "Investigate card top up fee",
        risk="MEDIUM",
    ),

    "top_up_by_cash_or_cheque": _action(
        "top_up_by_cash_or_cheque",
        "CHECK_CASH_CHEQUE_TOP_UP",
        "Check cash or cheque top up",
    ),

    "top_up_failed": _action(
        "top_up_failed",
        "INVESTIGATE_FAILED_TOP_UP",
        "Investigate failed top up",
    ),

    "top_up_limits": _action(
        "top_up_limits",
        "CHECK_TOP_UP_LIMITS",
        "Check top up limits",
    ),

    "top_up_reverted": _action(
        "top_up_reverted",
        "INVESTIGATE_REVERTED_TOP_UP",
        "Investigate reverted top up",
        risk="MEDIUM",
    ),

    "topping_up_by_card": _action(
        "topping_up_by_card",
        "TOP_UP_BY_CARD",
        "Top up by card",
        risk="MEDIUM",
    ),

    "verify_top_up": _action(
        "verify_top_up",
        "VERIFY_TOP_UP",
        "Verify top up",
        risk="MEDIUM",
    ),

    # --------------------------------------------------------
    # BALANCE / DEPOSITS
    # --------------------------------------------------------

    "balance_not_updated_after_cheque_or_cash_deposit": _action(
        "balance_not_updated_after_cheque_or_cash_deposit",
        "INVESTIGATE_CASH_DEPOSIT_BALANCE",
        "Investigate cash or cheque deposit balance",
        risk="MEDIUM",
    ),

    # --------------------------------------------------------
    # CURRENCY / EXCHANGE
    # --------------------------------------------------------

    "exchange_charge": _action(
        "exchange_charge",
        "INVESTIGATE_EXCHANGE_FEE",
        "Investigate exchange fee",
        risk="MEDIUM",
    ),

    "exchange_rate": _action(
        "exchange_rate",
        "CHECK_EXCHANGE_RATE",
        "Check exchange rate",
    ),

    "exchange_via_app": _action(
        "exchange_via_app",
        "EXCHANGE_CURRENCY",
        "Exchange currency",
        risk="MEDIUM",
    ),

    "fiat_currency_support": _action(
        "fiat_currency_support",
        "CHECK_FIAT_CURRENCY_SUPPORT",
        "Check supported fiat currencies",
    ),

    "wrong_exchange_rate_for_cash_withdrawal": _action(
        "wrong_exchange_rate_for_cash_withdrawal",
        "INVESTIGATE_CASH_EXCHANGE_RATE",
        "Investigate cash withdrawal exchange rate",
        risk="MEDIUM",
    ),
}
