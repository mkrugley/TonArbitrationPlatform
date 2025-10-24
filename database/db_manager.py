"""
Database Manager
Менеджер базы данных с полным функционалом
"""

import asyncpg
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.models import (
    User, Dispute, Arbiter, Evidence, Decision,
    DisputeStatus, DisputeCategory, ArbiterSpecialization, EvidenceType
)

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Менеджер базы данных PostgreSQL
    Использует пул соединений для эффективной работы
    """
    
    def __init__(self, database_url: str):
        """
        Инициализация менеджера
        
        Args:
            database_url: URL подключения к PostgreSQL
        """
        self.database_url = database_url
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(self):
        """Создание пула подключений к базе данных"""
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            logger.info("✅ Пул подключений к БД создан")
            
            # Создание таблиц при первом подключении
            await self.create_tables()
            
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к БД: {e}")
            raise
    
    async def disconnect(self):
        """Закрытие пула подключений"""
        if self.pool:
            await self.pool.close()
            logger.info("✅ Пул подключений закрыт")
    
    @asynccontextmanager
    async def acquire(self):
        """Контекстный менеджер для получения соединения из пула"""
        async with self.pool.acquire() as conn:
            yield conn
    
    async def create_tables(self):
        """
        Создание всех таблиц в базе данных
        Выполняется автоматически при подключении
        """
        async with self.pool.acquire() as conn:
            await conn.execute("""
                -- ТАБЛИЦА ПОЛЬЗОВАТЕЛЕЙ
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username VARCHAR(255),
                    full_name VARCHAR(255) NOT NULL,
                    wallet_address VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_arbiter BOOLEAN DEFAULT FALSE,
                    is_active BOOLEAN DEFAULT TRUE,
                    is_blocked BOOLEAN DEFAULT FALSE,
                    disputes_participated INT DEFAULT 0,
                    rating DECIMAL(3, 2) DEFAULT 3.0,
                    language VARCHAR(10) DEFAULT 'ru',
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CHECK (rating >= 0.0 AND rating <= 5.0)
                );
                
                -- ТАБЛИЦА СПОРОВ
                CREATE TABLE IF NOT EXISTS disputes (
                    dispute_id SERIAL PRIMARY KEY,
                    initiator_id BIGINT NOT NULL REFERENCES users(user_id),
                    respondent_id BIGINT REFERENCES users(user_id),
                    respondent_username VARCHAR(255),
                    amount DECIMAL(12, 2) NOT NULL CHECK (amount > 0),
                    description TEXT NOT NULL,
                    category VARCHAR(50) NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    arbiter_id BIGINT REFERENCES users(user_id),
                    contract_address VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    initiator_deposit_paid BOOLEAN DEFAULT FALSE,
                    respondent_deposit_paid BOOLEAN DEFAULT FALSE,
                    resolution TEXT,
                    initiator_share INT CHECK (initiator_share >= 0 AND initiator_share <= 100)
                );
                
                -- ТАБЛИЦА АРБИТРОВ
                CREATE TABLE IF NOT EXISTS arbiters (
                    user_id BIGINT PRIMARY KEY REFERENCES users(user_id),
                    specialization VARCHAR(50) NOT NULL,
                    deposit_amount DECIMAL(12, 2) NOT NULL,
                    wallet_address VARCHAR(100),
                    is_active BOOLEAN DEFAULT TRUE,
                    rating DECIMAL(3, 2) DEFAULT 3.0,
                    cases_resolved INT DEFAULT 0,
                    appeals_count INT DEFAULT 0,
                    average_resolution_time DECIMAL(5, 2) DEFAULT 0.0,
                    total_earned DECIMAL(12, 2) DEFAULT 0.0,
                    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CHECK (rating >= 0.0 AND rating <= 5.0)
                );
                
                -- ТАБЛИЦА ДОКАЗАТЕЛЬСТВ
                CREATE TABLE IF NOT EXISTS evidence (
                    evidence_id SERIAL PRIMARY KEY,
                    dispute_id INT NOT NULL REFERENCES disputes(dispute_id) ON DELETE CASCADE,
                    user_id BIGINT NOT NULL REFERENCES users(user_id),
                    evidence_type VARCHAR(20) NOT NULL,
                    description TEXT NOT NULL,
                    file_path TEXT,
                    file_hash VARCHAR(64),
                    file_url TEXT,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- ТАБЛИЦА РЕШЕНИЙ
                CREATE TABLE IF NOT EXISTS decisions (
                    decision_id SERIAL PRIMARY KEY,
                    dispute_id INT NOT NULL REFERENCES disputes(dispute_id) ON DELETE CASCADE,
                    arbiter_id BIGINT NOT NULL REFERENCES users(user_id),
                    initiator_share INT NOT NULL CHECK (initiator_share >= 0 AND initiator_share <= 100),
                    reasoning TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_appealed BOOLEAN DEFAULT FALSE
                );
                
                -- ИНДЕКСЫ ДЛЯ ОПТИМИЗАЦИИ
                CREATE INDEX IF NOT EXISTS idx_disputes_status ON disputes(status);
                CREATE INDEX IF NOT EXISTS idx_disputes_initiator ON disputes(initiator_id);
                CREATE INDEX IF NOT EXISTS idx_disputes_respondent ON disputes(respondent_id);
                CREATE INDEX IF NOT EXISTS idx_disputes_arbiter ON disputes(arbiter_id);
                CREATE INDEX IF NOT EXISTS idx_disputes_created ON disputes(created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_evidence_dispute ON evidence(dispute_id);
                CREATE INDEX IF NOT EXISTS idx_arbiters_active ON arbiters(is_active);
                CREATE INDEX IF NOT EXISTS idx_arbiters_rating ON arbiters(rating DESC);
            """)
            
            logger.info("✅ Все таблицы созданы/проверены")
    
    # ========================================
    # МЕТОДЫ ДЛЯ РАБОТЫ С ПОЛЬЗОВАТЕЛЯМИ
    # ========================================
    
    async def create_user(self, user: User) -> int:
        """Создание или обновление пользователя"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO users (
                    user_id, username, full_name, created_at, 
                    language, last_activity
                )
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (user_id) DO UPDATE
                SET username = EXCLUDED.username,
                    full_name = EXCLUDED.full_name,
                    last_activity = EXCLUDED.last_activity
            """, 
                user.user_id, 
                user.username, 
                user.full_name, 
                user.created_at,
                user.language,
                user.last_activity
            )
            logger.info(f"✅ Пользователь {user.user_id} создан/обновлён")
            return user.user_id
    
    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получение пользователя по ID"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM users WHERE user_id = $1",
                user_id
            )
            return dict(row) if row else None
    
    async def update_user_wallet(self, user_id: int, wallet_address: str):
        """Обновление адреса кошелька пользователя"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE users 
                SET wallet_address = $1 
                WHERE user_id = $2
            """, wallet_address, user_id)
            logger.info(f"✅ Кошелёк пользователя {user_id} обновлён")
    
    async def update_user_activity(self, user_id: int):
        """Обновление времени последней активности"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE users 
                SET last_activity = $1 
                WHERE user_id = $2
            """, datetime.utcnow(), user_id)
    
    async def get_all_users_count(self) -> int:
        """Получение общего количества пользователей"""
        async with self.pool.acquire() as conn:
            count = await conn.fetchval("SELECT COUNT(*) FROM users")
            return count
    
    # ========================================
    # МЕТОДЫ ДЛЯ РАБОТЫ СО СПОРАМИ
    # ========================================
    
    async def create_dispute(self, dispute: Dispute) -> int:
        """Создание нового спора"""
        async with self.pool.acquire() as conn:
            dispute_id = await conn.fetchval("""
                INSERT INTO disputes (
                    initiator_id, amount, description, category, 
                    status, respondent_username, created_at, updated_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING dispute_id
            """,
                dispute.initiator_id,
                dispute.amount,
                dispute.description,
                dispute.category.value,
                dispute.status.value,
                dispute.respondent_username,
                dispute.created_at,
                dispute.updated_at
            )
            logger.info(f"✅ Создан спор #{dispute_id}")
            return dispute_id
    
    async def get_dispute(self, dispute_id: int) -> Optional[Dict[str, Any]]:
        """Получение спора по ID"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM disputes WHERE dispute_id = $1",
                dispute_id
            )
            return dict(row) if row else None
    
    async def update_dispute_status(
        self, 
        dispute_id: int, 
        status: DisputeStatus
    ):
        """Обновление статуса спора"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE disputes 
                SET status = $1, updated_at = $2
                WHERE dispute_id = $3
            """, status.value, datetime.utcnow(), dispute_id)
            
            logger.info(f"📝 Спор #{dispute_id} -> {status.value}")
    
    async def update_dispute_respondent(
        self,
        dispute_id: int,
        respondent_id: int
    ):
        """Добавление ответчика в спор"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE disputes 
                SET respondent_id = $1,
                    status = $2,
                    updated_at = $3
                WHERE dispute_id = $4
            """,
                respondent_id,
                DisputeStatus.AWAITING_DEPOSITS.value,
                datetime.utcnow(),
                dispute_id
            )
            logger.info(f"✅ К спору #{dispute_id} добавлен ответчик {respondent_id}")
    
    async def update_dispute_arbiter(
        self,
        dispute_id: int,
        arbiter_id: int
    ):
        """Назначение арбитра на спор"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE disputes 
                SET arbiter_id = $1,
                    status = $2,
                    updated_at = $3
                WHERE dispute_id = $4
            """,
                arbiter_id,
                DisputeStatus.UNDER_REVIEW.value,
                datetime.utcnow(),
                dispute_id
            )
            logger.info(f"⚖️ Спор #{dispute_id} назначен арбитру {arbiter_id}")
    
    async def get_user_disputes(
        self,
        user_id: int,
        as_initiator: bool = True,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Получение списка споров пользователя"""
        async with self.pool.acquire() as conn:
            column = "initiator_id" if as_initiator else "respondent_id"
            rows = await conn.fetch(f"""
                SELECT * FROM disputes 
                WHERE {column} = $1
                ORDER BY created_at DESC
                LIMIT $2
            """, user_id, limit)
            return [dict(row) for row in rows]
    
    async def get_arbiter_disputes(
        self,
        arbiter_id: int,
        status: Optional[DisputeStatus] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Получение споров арбитра"""
        async with self.pool.acquire() as conn:
            if status:
                rows = await conn.fetch("""
                    SELECT * FROM disputes 
                    WHERE arbiter_id = $1 AND status = $2
                    ORDER BY created_at DESC
                    LIMIT $3
                """, arbiter_id, status.value, limit)
            else:
                rows = await conn.fetch("""
                    SELECT * FROM disputes 
                    WHERE arbiter_id = $1
                    ORDER BY created_at DESC
                    LIMIT $2
                """, arbiter_id, limit)
            
            return [dict(row) for row in rows]
    
    async def get_all_disputes_count(self) -> int:
        """Получение общего количества споров"""
        async with self.pool.acquire() as conn:
            count = await conn.fetchval("SELECT COUNT(*) FROM disputes")
            return count
    
    # ========================================
    # МЕТОДЫ ДЛЯ РАБОТЫ С АРБИТРАМИ
    # ========================================
    
    async def create_arbiter(self, arbiter: Arbiter) -> int:
        """Регистрация нового арбитра"""
        async with self.pool.acquire() as conn:
            # Обновляем статус пользователя
            await conn.execute("""
                UPDATE users SET is_arbiter = TRUE WHERE user_id = $1
            """, arbiter.user_id)
            
            # Создаём запись арбитра
            await conn.execute("""
                INSERT INTO arbiters (
                    user_id, specialization, deposit_amount, 
                    wallet_address, registered_at
                )
                VALUES ($1, $2, $3, $4, $5)
            """,
                arbiter.user_id,
                arbiter.specialization.value,
                arbiter.deposit_amount,
                arbiter.wallet_address,
                arbiter.registered_at
            )
            logger.info(f"⚖️ Зарегистрирован арбитр {arbiter.user_id}")
            return arbiter.user_id
    
    async def get_arbiter(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получение информации об арбитре"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM arbiters WHERE user_id = $1",
                user_id
            )
            return dict(row) if row else None
    
    async def get_available_arbiters(
        self,
        specialization: Optional[ArbiterSpecialization] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Получение списка доступных арбитров"""
        async with self.pool.acquire() as conn:
            if specialization:
                rows = await conn.fetch("""
                    SELECT a.*, u.full_name, u.username
                    FROM arbiters a
                    JOIN users u ON a.user_id = u.user_id
                    WHERE a.is_active = TRUE 
                      AND (a.specialization = $1 OR a.specialization = 'general')
                    ORDER BY a.rating DESC, a.cases_resolved DESC
                    LIMIT $2
                """, specialization.value, limit)
            else:
                rows = await conn.fetch("""
                    SELECT a.*, u.full_name, u.username
                    FROM arbiters a
                    JOIN users u ON a.user_id = u.user_id
                    WHERE a.is_active = TRUE
                    ORDER BY a.rating DESC, a.cases_resolved DESC
                    LIMIT $1
                """, limit)
            
            return [dict(row) for row in rows]
    
    async def update_arbiter_stats(
        self,
        arbiter_id: int,
        cases_increment: int = 1,
        earned_amount: float = 0.0
    ):
        """Обновление статистики арбитра"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE arbiters
                SET cases_resolved = cases_resolved + $1,
                    total_earned = total_earned + $2
                WHERE user_id = $3
            """, cases_increment, earned_amount, arbiter_id)
    
    # ========================================
    # МЕТОДЫ ДЛЯ РАБОТЫ С ДОКАЗАТЕЛЬСТВАМИ
    # ========================================
    
    async def add_evidence(self, evidence: Evidence) -> int:
        """Добавление доказательства"""
        async with self.pool.acquire() as conn:
            evidence_id = await conn.fetchval("""
                INSERT INTO evidence (
                    dispute_id, user_id, evidence_type, description,
                    file_path, file_hash, file_url, uploaded_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING evidence_id
            """,
                evidence.dispute_id,
                evidence.user_id,
                evidence.file_type.value,
                evidence.description,
                evidence.file_path,
                evidence.file_hash,
                evidence.file_url,
                evidence.uploaded_at
            )
            logger.info(f"📎 Добавлено доказательство #{evidence_id} к спору #{evidence.dispute_id}")
            return evidence_id
    
    async def get_dispute_evidence(
        self,
        dispute_id: int
    ) -> List[Dict[str, Any]]:
        """Получение всех доказательств по спору"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT e.*, u.full_name, u.username
                FROM evidence e
                JOIN users u ON e.user_id = u.user_id
                WHERE e.dispute_id = $1
                ORDER BY e.uploaded_at ASC
            """, dispute_id)
            return [dict(row) for row in rows]
    
    # ========================================
    # МЕТОДЫ ДЛЯ РАБОТЫ С РЕШЕНИЯМИ
    # ========================================
    
    async def create_decision(self, decision: Decision) -> int:
        """Создание решения арбитра"""
        async with self.pool.acquire() as conn:
            decision_id = await conn.fetchval("""
                INSERT INTO decisions (
                    dispute_id, arbiter_id, initiator_share, 
                    reasoning, created_at
                )
                VALUES ($1, $2, $3, $4, $5)
                RETURNING decision_id
            """,
                decision.dispute_id,
                decision.arbiter_id,
                decision.initiator_share,
                decision.reasoning,
                decision.created_at
            )
            
            # Обновляем спор
            await conn.execute("""
                UPDATE disputes 
                SET status = $1,
                    initiator_share = $2,
                    resolution = $3,
                    updated_at = $4
                WHERE dispute_id = $5
            """,
                DisputeStatus.RESOLVED.value,
                decision.initiator_share,
                decision.reasoning,
                datetime.utcnow(),
                decision.dispute_id
            )
            
            logger.info(f"✅ Решение #{decision_id} для спора #{decision.dispute_id}")
            return decision_id
    
    # ========================================
    # СТАТИСТИКА И АНАЛИТИКА
    # ========================================
    
    async def get_platform_stats(self) -> Dict[str, Any]:
        """Получение общей статистики платформы"""
        async with self.pool.acquire() as conn:
            stats = {}
            
            stats['total_users'] = await conn.fetchval(
                "SELECT COUNT(*) FROM users"
            )
            
            stats['total_disputes'] = await conn.fetchval(
                "SELECT COUNT(*) FROM disputes"
            )
            
            stats['total_arbiters'] = await conn.fetchval(
                "SELECT COUNT(*) FROM arbiters WHERE is_active = TRUE"
            )
            
            stats['resolved_disputes'] = await conn.fetchval(
                "SELECT COUNT(*) FROM disputes WHERE status = $1",
                DisputeStatus.RESOLVED.value
            )
            
            total_amount = await conn.fetchval(
                "SELECT SUM(amount) FROM disputes"
            )
            stats['total_amount'] = float(total_amount) if total_amount else 0.0
            
            return stats
