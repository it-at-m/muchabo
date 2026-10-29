package de.muenchen.oss.refarch.backend.model;

import de.muenchen.oss.refarch.backend.common.BaseEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import lombok.EqualsAndHashCode;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import lombok.ToString;

@Entity
@Getter
@Setter
@ToString(callSuper = true)
@EqualsAndHashCode(callSuper = true)
@NoArgsConstructor
public class Model extends BaseEntity {

    private static final long serialVersionUID = 1L;

    @Column(name = "model_name", nullable = false, unique = true, length = 100)
    private String modelName;
}
