"""create orders table

之前 orders 表只存在于第一章的 SQL 脚本里,没有进迁移。
后果: 本地库有(手工建过), 但全新库(CI / Docker 空卷)没有,
      删除用户时 ORM 会去加载 user.orders, 于是报 Table doesn't exist。

这个迁移把它补上, 让"只跑 alembic upgrade head"就能得到完整表结构。

Revision ID: 0004_orders
Revises: 0003_password
Create Date: 2026-11-10
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision = "0004_orders"
down_revision = "0003_password"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "orders",
        sa.Column("id", mysql.INTEGER(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("order_no", sa.String(32), nullable=False, comment="订单号"),
        sa.Column("user_id", mysql.INTEGER(unsigned=True), nullable=False, comment="下单用户ID"),
        sa.Column("total_amount", sa.Numeric(10, 2), nullable=False, comment="订单总金额"),
        sa.Column(
            "status",
            mysql.TINYINT(),
            server_default=sa.text("0"),
            nullable=False,
            comment="状态:0待支付,1已支付,2已发货",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_no"),
        comment="订单主表",
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )


def downgrade() -> None:
    op.drop_table("orders")
