package ads.annotation;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/**
 * Marks a class as a sensor/domain-function service so the M2M lifts its
 * public methods into RoboChart {@code function} declarations, regardless
 * of whether the class name contains the substring {@code "sensor"}.
 */
@Retention(RetentionPolicy.SOURCE)
@Target(ElementType.TYPE)
public @interface SensorService {
}
