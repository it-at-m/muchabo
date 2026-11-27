package de.muenchen.oss.refarch.backend;

import static de.muenchen.oss.refarch.backend.TestConstants.SPRING_TEST_PROFILE;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import de.muenchen.oss.refarch.backend.chatbot.Chatbot;
import de.muenchen.oss.refarch.backend.chatbot.ChatbotConfig;
import de.muenchen.oss.refarch.backend.mcp.ChatbotTool;
import de.muenchen.oss.refarch.backend.mcp.McpServer;
import de.muenchen.oss.refarch.backend.mcp.McpTool;
import de.muenchen.oss.refarch.backend.model.Model;
import jakarta.persistence.EntityManager;
import jakarta.persistence.PersistenceException;
import java.util.UUID;
import org.hibernate.HibernateException;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.testcontainers.service.connection.ServiceConnection;
import org.springframework.context.annotation.Import;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.support.TransactionTemplate;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import org.testcontainers.postgresql.PostgreSQLContainer;
import org.testcontainers.utility.DockerImageName;

/**
 * Verifies the schema-level rules of the chatbot/MCP core domain against the Flyway-managed
 * schema (V001–V003), as specified in specs/001-specify-core-domain/spec.md. Unlike the default
 * test profile, Hibernate only validates (ddl-auto=validate) so the assertions cover the real
 * migration-defined constraints: uniqueness, mandatory references, length limits, delete
 * cascades and the active-flag default.
 */
@Testcontainers
@SpringBootTest(
        properties = {
                "spring.jpa.hibernate.ddl-auto=validate",
                "spring.flyway.locations=classpath:db/migration/schema"
        }
)
@ActiveProfiles(profiles = { SPRING_TEST_PROFILE })
@Import(TestSecurityConfiguration.class)
class CoreDomainSchemaIntegrationTest {

    @Container
    @ServiceConnection
    @SuppressWarnings("unused")
    private static final PostgreSQLContainer POSTGRE_SQL_CONTAINER = new PostgreSQLContainer(
            DockerImageName.parse(TestUtils.getImageFromDockerCompose("postgres")));

    @Autowired
    private EntityManager entityManager;

    @Autowired
    private PlatformTransactionManager transactionManager;

    private TransactionTemplate txTemplate;

    @BeforeEach
    void setUp() {
        txTemplate = new TransactionTemplate(transactionManager);
        // Remove leftover rows in FK-safe order; each test commits its own transactions.
        txTemplate.executeWithoutResult(status -> {
            entityManager.createQuery("DELETE FROM ChatbotTool").executeUpdate();
            entityManager.createQuery("DELETE FROM ChatbotConfig").executeUpdate();
            entityManager.createQuery("DELETE FROM McpTool").executeUpdate();
            entityManager.createQuery("DELETE FROM McpServer").executeUpdate();
            entityManager.createQuery("DELETE FROM Chatbot").executeUpdate();
            entityManager.createQuery("DELETE FROM Model").executeUpdate();
            entityManager.createQuery("DELETE FROM TheEntity").executeUpdate();
        });
    }

    // FR-002: chatbot names need not be unique; model names must be.
    @Test
    void givenChatbotsAndModelsWithSameName_thenOnlyModelNamesAreUnique() {
        txTemplate.executeWithoutResult(status -> {
            persistChatbot("Same Name");
            persistChatbot("Same Name");
            entityManager.flush();
        });
        assertFlushViolates(() -> {
            persistModel("Same Name");
            persistModel("Same Name");
            entityManager.flush();
        });
    }

    // FR-003, FR-012: a configuration requires an existing chatbot and an existing model.
    @Test
    void givenConfigurationWithoutValidReferences_thenPersistenceIsRejected() {
        assertFlushViolates(() -> {
            final Chatbot chatbot = persistChatbot("bot");
            final Model model = persistModel("model");
            final ChatbotConfig config = validConfig(chatbot, model);
            config.setChatbot(null);
            entityManager.persist(config);
            entityManager.flush();
        });
        assertFlushViolates(() -> {
            final Chatbot chatbot = persistChatbot("bot");
            final Model missingModel = new Model();
            missingModel.setModelName("not persisted");
            missingModel.setId(UUID.randomUUID());
            final ChatbotConfig config = validConfig(chatbot, missingModel);
            entityManager.persist(config);
            entityManager.flush();
        });
    }

    // FR-004: creation timestamp is set automatically and preserved on regular updates.
    @Test
    void givenRegularConfigurationChange_thenCreationTimestampIsPreserved() {
        final UUID configId = txTemplate.execute(status -> {
            final ChatbotConfig config = validConfig(persistChatbot("bot"), persistModel("model"));
            entityManager.persist(config);
            entityManager.flush();
            return config.getId();
        });

        txTemplate.executeWithoutResult(status -> {
            final ChatbotConfig config = entityManager.find(ChatbotConfig.class, configId);
            assertThat(config.getCreatedAt()).isNotNull();
            final var originalTimestamp = config.getCreatedAt();
            config.setPrompt("changed prompt");
            entityManager.flush();
            entityManager.clear();
            assertThat(entityManager.find(ChatbotConfig.class, configId).getCreatedAt())
                    .isEqualTo(originalTimestamp);
        });
    }

    // FR-005: the same model and version label may recur in multiple configurations.
    @Test
    void givenSameModelAndVersion_thenMultipleConfigurationsAreAllowed() {
        txTemplate.executeWithoutResult(status -> {
            final Chatbot chatbot = persistChatbot("bot");
            final Model model = persistModel("model");
            final ChatbotConfig first = validConfig(chatbot, model);
            final ChatbotConfig second = validConfig(chatbot, model);
            entityManager.persist(first);
            entityManager.persist(second);
            entityManager.flush();
            assertThat(first.getId()).isNotEqualTo(second.getId());
        });
    }

    // FR-002, FR-003, FR-006: length limits of 100 (names), 255 (address) and 20 (version).
    @Test
    void givenValuesBeyondColumnLimits_thenPersistenceIsRejected() {
        assertFlushViolates(() -> {
            entityManager.persist(persistChatbot("x".repeat(101)));
            entityManager.flush();
        });
        assertFlushViolates(() -> {
            entityManager.persist(persistServer("server", "u".repeat(256)));
            entityManager.flush();
        });
        assertFlushViolates(() -> {
            final ChatbotConfig config = validConfig(persistChatbot("bot"), persistModel("model"));
            config.setVersion("v".repeat(21));
            entityManager.persist(config);
            entityManager.flush();
        });
    }

    // FR-008, FR-009: assignments are active by default; the configuration/tool pair is unique
    // regardless of the active flag.
    @Test
    void givenToolAssignment_thenItIsActiveByDefaultAndPairIsUnique() {
        final UUID assignmentId = txTemplate.execute(status -> {
            final Chatbot chatbot = persistChatbot("bot");
            final Model model = persistModel("model");
            final McpServer server = persistServer("server", "https://mcp.example.org");
            final McpTool tool = persistTool(server, "tool");
            final ChatbotConfig config = validConfig(chatbot, model);
            final ChatbotTool assignment = new ChatbotTool();
            assignment.setChatbotConfig(config);
            assignment.setMcpTool(tool);
            entityManager.persist(config);
            entityManager.persist(assignment);
            entityManager.flush();
            assertThat(assignment.isActive()).isTrue();
            return assignment.getId();
        });

        assertFlushViolates(() -> {
            final ChatbotTool duplicate = entityManager.find(ChatbotTool.class, assignmentId);
            final ChatbotTool second = new ChatbotTool();
            second.setChatbotConfig(duplicate.getChatbotConfig());
            second.setMcpTool(duplicate.getMcpTool());
            second.setActive(false);
            entityManager.persist(second);
            entityManager.flush();
        });
    }

    // FR-010: deleting a chatbot is prevented while a configuration references it.
    @Test
    void givenChatbotWithConfiguration_thenDeletionIsPrevented() {
        final UUID chatbotId = txTemplate.execute(status -> {
            final Chatbot chatbot = persistChatbot("bot");
            final Model model = persistModel("model");
            final ChatbotConfig config = validConfig(chatbot, model);
            entityManager.persist(config);
            entityManager.flush();
            return chatbot.getId();
        });

        assertFlushViolates(() -> {
            entityManager.remove(entityManager.find(Chatbot.class, chatbotId));
            entityManager.flush();
        });
    }

    // FR-011: deleting configuration, tool or server removes dependent assignments only.
    @Test
    void givenDeletionOfConfigToolOrServer_thenOnlyAssignmentsAreRemoved() {
        final UUID chatbotId = txTemplate.execute(status -> {
            final Chatbot chatbot = persistChatbot("bot");
            final Model model = persistModel("model");
            final McpServer server = persistServer("server", "https://mcp.example.org");
            final McpTool tool = persistTool(server, "tool");
            final ChatbotConfig config = validConfig(chatbot, model);
            final ChatbotTool assignment = new ChatbotTool();
            assignment.setChatbotConfig(config);
            assignment.setMcpTool(tool);
            entityManager.persist(config);
            entityManager.persist(assignment);
            entityManager.flush();
            entityManager.clear();

            // Deleting the configuration removes only its assignments.
            entityManager.remove(entityManager.find(ChatbotConfig.class, config.getId()));
            entityManager.flush();
            entityManager.clear();
            assertThat(count(ChatbotTool.class)).isZero();
            assertThat(entityManager.find(Chatbot.class, chatbot.getId())).isNotNull();
            assertThat(entityManager.find(McpTool.class, tool.getId())).isNotNull();

            // Deleting the tool removes its (already removed) assignments; the server remains.
            entityManager.remove(entityManager.find(McpTool.class, tool.getId()));
            entityManager.flush();
            entityManager.clear();
            assertThat(entityManager.find(McpServer.class, server.getId())).isNotNull();

            // Deleting the server removes its tools via the database cascade.
            entityManager.remove(entityManager.find(McpServer.class, server.getId()));
            entityManager.flush();
            entityManager.clear();
            assertThat(count(McpTool.class)).isZero();
            assertThat(count(ChatbotTool.class)).isZero();
            return chatbot.getId();
        });
        assertThat(chatbotId).isNotNull();
    }

    private long count(final Class<?> entityType) {
        return entityManager
                .createQuery("SELECT COUNT(e) FROM " + entityType.getSimpleName() + " e", Long.class)
                .getSingleResult();
    }

    private void assertFlushViolates(final Runnable violatingAction) {
        assertThatThrownBy(() -> txTemplate.executeWithoutResult(status -> violatingAction.run()))
                .isInstanceOfAny(PersistenceException.class, HibernateException.class);
    }

    private Chatbot persistChatbot(final String name) {
        final Chatbot chatbot = new Chatbot();
        chatbot.setName(name);
        entityManager.persist(chatbot);
        return chatbot;
    }

    private Model persistModel(final String name) {
        final Model model = new Model();
        model.setModelName(name);
        entityManager.persist(model);
        return model;
    }

    private McpServer persistServer(final String name, final String url) {
        final McpServer server = new McpServer();
        server.setName(name);
        server.setUrl(url);
        entityManager.persist(server);
        return server;
    }

    private McpTool persistTool(final McpServer server, final String name) {
        final McpTool tool = new McpTool();
        tool.setMcpServer(server);
        tool.setName(name);
        entityManager.persist(tool);
        return tool;
    }

    private ChatbotConfig validConfig(final Chatbot chatbot, final Model model) {
        final ChatbotConfig config = new ChatbotConfig();
        config.setChatbot(chatbot);
        config.setModel(model);
        config.setPrompt("prompt");
        config.setTemperature(0.7);
        config.setVersion("v1");
        return config;
    }
}
