package de.muenchen.oss.refarch.backend.mcp;

import de.muenchen.oss.refarch.backend.chatbot.ChatbotConfig;
import de.muenchen.oss.refarch.backend.common.BaseEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import jakarta.persistence.UniqueConstraint;
import lombok.EqualsAndHashCode;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import lombok.ToString;

@Entity
@Table(name = "chatbot_tool", uniqueConstraints = { @UniqueConstraint(name = "uq_chatbot_config_tool", columnNames = { "chatbot_config_id", "mcp_tool_id" }) })
@Getter
@Setter
@ToString(callSuper = true)
@EqualsAndHashCode(callSuper = true)
@NoArgsConstructor
public class ChatbotTool extends BaseEntity {

    private static final long serialVersionUID = 1L;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "mcp_tool_id", nullable = false)
    @ToString.Exclude
    @EqualsAndHashCode.Exclude
    private McpTool mcpTool;

    @Column(name = "is_active", nullable = false)
    private boolean isActive = true;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "chatbot_config_id", nullable = false)
    @ToString.Exclude
    @EqualsAndHashCode.Exclude
    private ChatbotConfig chatbotConfig;
}
