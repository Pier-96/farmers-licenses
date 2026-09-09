from alembic import op
import sqlalchemy as sa
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('licenses',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('product_id', sa.String(64), nullable=False),
        sa.Column('key_hash', sa.String(64), nullable=False, unique=True),
        sa.Column('key_prefix', sa.String(4), nullable=False),
        sa.Column('status', sa.String(16), nullable=False),
        sa.Column('machine_id', sa.String(64)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('activated_at', sa.DateTime(timezone=True)),
        sa.Column('last_validation_at', sa.DateTime(timezone=True)),
        sa.Column('activation_count', sa.Integer(), nullable=False),
        sa.Column('max_activations', sa.Integer(), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True)),
        sa.Column('notes', sa.String(2000)),
        sa.CheckConstraint("status IN ('unused','active','revoked')", name='license_status'),
        sa.CheckConstraint('activation_count >= 0 AND max_activations >= 1', name='activation_limits'))
    op.create_index('ix_licenses_product_id', 'licenses', ['product_id'])

def downgrade():
    op.drop_table('licenses')
