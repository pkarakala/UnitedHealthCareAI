"""initial schema

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Patients
    op.create_table(
        'patients',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('first_name', sa.String(255), nullable=False),
        sa.Column('last_name', sa.String(255), nullable=False),
        sa.Column('date_of_birth', sa.Date, nullable=False),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('address', sa.JSON, nullable=True),
        sa.Column('member_id', sa.String(50), nullable=True, index=True),
        sa.Column('group_number', sa.String(50), nullable=True),
        sa.Column('insurance_id', sa.String(36), sa.ForeignKey('insurances.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(255), nullable=True),
    )

    # Insurances
    op.create_table(
        'insurances',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('plan_name', sa.String(255), nullable=False),
        sa.Column('payer_name', sa.String(255), nullable=True),
        sa.Column('bin_number', sa.String(10), nullable=True),
        sa.Column('pcn', sa.String(20), nullable=True),
        sa.Column('group_number', sa.String(50), nullable=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('fax', sa.String(20), nullable=True),
        sa.Column('portal_url', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('formulary_data', sa.JSON, nullable=True),
        sa.Column('pa_requirements', sa.JSON, nullable=True),
        sa.Column('step_therapy_rules', sa.JSON, nullable=True),
        sa.Column('quantity_limits', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(255), nullable=True),
    )

    # Prescriptions
    op.create_table(
        'prescriptions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('patient_id', sa.String(36), sa.ForeignKey('patients.id'), nullable=False),
        sa.Column('prescriber_npi', sa.String(10), nullable=False),
        sa.Column('prescriber_name', sa.String(255), nullable=True),
        sa.Column('prescriber_phone', sa.String(20), nullable=True),
        sa.Column('prescriber_fax', sa.String(20), nullable=True),
        sa.Column('drug_name', sa.String(255), nullable=False),
        sa.Column('ndc', sa.String(11), nullable=True),
        sa.Column('strength', sa.String(50), nullable=True),
        sa.Column('quantity', sa.Integer, nullable=True),
        sa.Column('days_supply', sa.Integer, nullable=True),
        sa.Column('refills', sa.Integer, nullable=True),
        sa.Column('directions', sa.Text, nullable=True),
        sa.Column('diagnosis_codes', sa.JSON, nullable=True),
        sa.Column('pharmacy_npi', sa.String(10), nullable=True),
        sa.Column('date_written', sa.Date, nullable=True),
        sa.Column('raw_image_url', sa.String(500), nullable=True),
        sa.Column('ocr_confidence', sa.Float, nullable=True),
        sa.Column('source', sa.String(50), nullable=True),
        sa.Column('status', sa.String(50), default='intake'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(255), nullable=True),
    )

    # Prior Authorizations
    op.create_table(
        'prior_auths',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('patient_id', sa.String(36), sa.ForeignKey('patients.id'), nullable=False),
        sa.Column('prescription_id', sa.String(36), sa.ForeignKey('prescriptions.id'), nullable=False),
        sa.Column('insurance_id', sa.String(36), sa.ForeignKey('insurances.id'), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, index=True),
        sa.Column('sub_status', sa.String(100), nullable=True),
        sa.Column('pa_number', sa.String(100), unique=True, nullable=True),
        sa.Column('confirmation_number', sa.String(100), nullable=True),
        sa.Column('submission_method', sa.String(50), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('decision_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expected_response_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('decision', sa.String(50), nullable=True),
        sa.Column('denial_reason', sa.Text, nullable=True),
        sa.Column('denial_codes', sa.JSON, nullable=True),
        sa.Column('medical_necessity_letter', sa.Text, nullable=True),
        sa.Column('clinical_summary', sa.Text, nullable=True),
        sa.Column('required_documents', sa.JSON, nullable=True),
        sa.Column('collected_documents', sa.JSON, nullable=True),
        sa.Column('claim_amount', sa.Numeric(10, 2), nullable=True),
        sa.Column('revenue_recovered', sa.Numeric(10, 2), nullable=True),
        sa.Column('current_agent', sa.String(50), nullable=True),
        sa.Column('retry_count', sa.Integer, default=0),
        sa.Column('max_retries', sa.Integer, default=3),
        sa.Column('escalated', sa.Boolean, default=False),
        sa.Column('assigned_to', sa.String(255), nullable=True),
        sa.Column('priority', sa.Integer, default=5),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(255), nullable=True),
    )

    # Clinical Documents
    op.create_table(
        'clinical_documents',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('prior_auth_id', sa.String(36), sa.ForeignKey('prior_auths.id'), nullable=False),
        sa.Column('document_type', sa.String(50), nullable=False),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('file_size', sa.Integer, nullable=True),
        sa.Column('mime_type', sa.String(100), nullable=True),
        sa.Column('content_text', sa.Text, nullable=True),
        sa.Column('ocr_text', sa.Text, nullable=True),
        sa.Column('metadata_json', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(255), nullable=True),
    )

    # Communications
    op.create_table(
        'communications',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('prior_auth_id', sa.String(36), sa.ForeignKey('prior_auths.id'), nullable=False),
        sa.Column('channel', sa.String(20), nullable=False),
        sa.Column('direction', sa.String(10), default='outbound'),
        sa.Column('recipient', sa.String(255), nullable=False),
        sa.Column('subject', sa.String(500), nullable=True),
        sa.Column('body', sa.Text, nullable=True),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('external_id', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(255), nullable=True),
    )

    # Appeals
    op.create_table(
        'appeals',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('prior_auth_id', sa.String(36), sa.ForeignKey('prior_auths.id'), nullable=False),
        sa.Column('appeal_number', sa.String(100), nullable=True),
        sa.Column('level', sa.Integer, default=1),
        sa.Column('status', sa.String(50), default='draft'),
        sa.Column('denial_reason', sa.Text, nullable=True),
        sa.Column('denial_codes', sa.JSON, nullable=True),
        sa.Column('appeal_strategy', sa.Text, nullable=True),
        sa.Column('appeal_letter', sa.Text, nullable=True),
        sa.Column('supporting_evidence', sa.JSON, nullable=True),
        sa.Column('clinical_references', sa.JSON, nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('decision_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('decision', sa.String(50), nullable=True),
        sa.Column('decision_notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(255), nullable=True),
    )

    # Audit Logs
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('user_id', sa.String(255), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=False),
        sa.Column('resource_id', sa.String(36), nullable=True),
        sa.Column('details', sa.JSON, nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('phi_accessed', sa.Boolean, default=False),
        sa.Column('data_before', sa.Text, nullable=True),
        sa.Column('data_after', sa.Text, nullable=True),
    )

    # Agent Executions
    op.create_table(
        'agent_executions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('prior_auth_id', sa.String(36), sa.ForeignKey('prior_auths.id'), nullable=False),
        sa.Column('agent_name', sa.String(50), nullable=False, index=True),
        sa.Column('status', sa.String(20), default='running'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_ms', sa.Integer, nullable=True),
        sa.Column('input_data', sa.JSON, nullable=True),
        sa.Column('output_data', sa.JSON, nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('tokens_input', sa.Integer, nullable=True),
        sa.Column('tokens_output', sa.Integer, nullable=True),
        sa.Column('model_used', sa.String(50), nullable=True),
        sa.Column('cost_usd', sa.Float, nullable=True),
        sa.Column('trace_id', sa.String(100), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('agent_executions')
    op.drop_table('audit_logs')
    op.drop_table('appeals')
    op.drop_table('communications')
    op.drop_table('clinical_documents')
    op.drop_table('prior_auths')
    op.drop_table('prescriptions')
    op.drop_table('patients')
    op.drop_table('insurances')
