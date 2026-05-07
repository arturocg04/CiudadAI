// Para añadir lógica JS que no quieras incluir globalmente en `app.js`.
// Se asume que `base.html` define el bloque `extra_js` para incluir este archivo cuando convenga.

/* =====================================================
   page.js - Micro-interacciones y manejo de transiciones
   ===================================================== */

(function() {
  'use strict';

  // =====================================================
  // 1. INICIALIZACIÓN Y DETECTORES
  // =====================================================

  const config = {
    animationDuration: 300,
    transitionDelay: 100,
    reduceMotion: window.matchMedia('(prefers-reduced-motion: reduce)').matches,
  };

  // Detectar preferencia de movimiento reducido
  window.matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change', (e) => {
    config.reduceMotion = e.matches;
  });

  // =====================================================
  // 2. UTILITIES
  // =====================================================

  const u = {
    // Agregar clase con transición
    addClass: (el, className) => {
      if (el) el.classList.add(className);
    },

    removeClass: (el, className) => {
      if (el) el.classList.remove(className);
    },

    toggleClass: (el, className) => {
      if (el) el.classList.toggle(className);
    },

    hasClass: (el, className) => {
      return el ? el.classList.contains(className) : false;
    },

    // Esperar a que una animación termine
    onAnimationEnd: (el, callback) => {
      if (!el) return;
      const handler = () => {
        el.removeEventListener('animationend', handler);
        if (callback) callback();
      };
      el.addEventListener('animationend', handler);
    },

    // Esperar a que una transición termine
    onTransitionEnd: (el, callback) => {
      if (!el) return;
      const handler = () => {
        el.removeEventListener('transitionend', handler);
        if (callback) callback();
      };
      el.addEventListener('transitionend', handler);
    },
  };

  // =====================================================
  // 3. FADE-IN ANIMATIONS EN CARGA DE PÁGINA
  // =====================================================

  const initPageAnimations = () => {
    // Asegurar que main está visible
    const main = document.querySelector('main');
    if (main) {
      main.style.opacity = '1';
      main.style.animation = 'fadeIn 0.5s ease-out';
    }

    // Animar elementos del DOM
    const animatedElements = document.querySelectorAll(
      '[data-animate], .card, [class*="card"], form, .content-box'
    );

    animatedElements.forEach((el, index) => {
      if (config.reduceMotion) {
        el.style.animation = 'none';
        el.style.opacity = '1';
      } else {
        el.style.opacity = '0';
        el.style.animation = `fadeInUp 0.6s ease-out forwards`;
        el.style.animationDelay = `${index * 0.1}s`;
      }
    });
  };

  // =====================================================
  // 4. FORM ENHANCEMENTS
  // =====================================================

  const initFormEnhancements = () => {
    const forms = document.querySelectorAll('form');

    forms.forEach((form) => {
      // Agregar indicador visual de foco
      form.addEventListener('focusin', (e) => {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
          e.target.parentElement?.style.setProperty('--focused', 'true');
        }
      });

      form.addEventListener('focusout', (e) => {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
          e.target.parentElement?.style.removeProperty('--focused');
        }
      });

      // Validación en tiempo real con visual feedback
      const inputs = form.querySelectorAll('input[required], textarea[required]');
      inputs.forEach((input) => {
        input.addEventListener('blur', () => validateField(input));
        input.addEventListener('change', () => validateField(input));
      });

      // Efecto visual al enviar
      const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
      if (submitBtn) {
        form.addEventListener('submit', (e) => {
          const isValid = form.checkValidity();
          if (isValid && !config.reduceMotion) {
            submitBtn.style.animation = 'pulseGlow 0.6s ease-out';
          }
        });
      }
    });
  };

  const validateField = (field) => {
    if (!field.checkValidity()) {
      field.style.borderColor = 'var(--color-error, #d32f2f)';
      field.style.boxShadow = '0 0 0 3px rgba(211, 47, 47, 0.1)';
    } else {
      field.style.borderColor = '';
      field.style.boxShadow = '';
    }
  };

  // =====================================================
  // 5. BUTTON INTERACTIONS
  // =====================================================



const initUnifiedButtonAndLinkInteractions = () => {
  // Selector unificado: botones Y enlaces que parecen botones
  const interactiveElements = document.querySelectorAll(
    'button, .btn, a.btn, a[class*="btn"], input[type="submit"], input[type="button"], [role="button"]'
  );

  interactiveElements.forEach((element) => {
    // =====================================================
    // 1. RIPPLE EFFECT (Click visual)
    // =====================================================
    element.addEventListener('click', function(e) {
      if (config.reduceMotion || this.disabled || this.getAttribute('aria-disabled') === 'true') return;

      const rect = this.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      // Crear elemento ripple
      const ripple = document.createElement('span');
      ripple.className = 'ripple';
      ripple.style.position = 'absolute';
      ripple.style.left = x + 'px';
      ripple.style.top = y + 'px';
      ripple.style.width = '0';
      ripple.style.height = '0';
      ripple.style.borderRadius = '50%';
      ripple.style.backgroundColor = 'rgba(255, 255, 255, 0.5)';
      ripple.style.pointerEvents = 'none';
      ripple.style.animation = 'rippleEffect 0.6s ease-out forwards';

      this.style.position = 'relative';
      this.style.overflow = 'hidden';
      this.appendChild(ripple);

      // Remover después de animación
      setTimeout(() => ripple.remove(), 600);
    });

    // =====================================================
    // 2. EFECTO DEGRADADO TRANSITORIO (Pulse al click)
    // =====================================================
    element.addEventListener('click', function(e) {
      if (config.reduceMotion) return;

      // Agregar clase con animación de pulse
      this.style.animation = 'none';
      
      // Trigger reflow para reiniciar animación
      void this.offsetWidth;
      
      this.style.animation = 'buttonPulse 0.6s ease-out';

      // Remover clase después de animación
      setTimeout(() => {
        this.style.animation = 'none';
      }, 600);
    });

    // =====================================================
    // 3. HOVER EFFECT (Elevación)
    // =====================================================
    element.addEventListener('mouseenter', function(e) {
      if (config.reduceMotion || this.disabled) return;

      this.style.transform = 'translateY(-3px)';
      this.style.boxShadow = '0 8px 24px rgba(31, 117, 94, 0.35)';
    });

    element.addEventListener('mouseleave', function(e) {
      if (config.reduceMotion) return;

      this.style.transform = 'translateY(0)';
      this.style.boxShadow = '0 4px 12px rgba(31, 117, 94, 0.2)';
    });

    // =====================================================
    // 4. ACTIVE STATE (Presión)
    // =====================================================
    element.addEventListener('mousedown', function(e) {
      if (config.reduceMotion || this.disabled) return;

      this.style.transform = 'translateY(-1px)';
      this.style.boxShadow = '0 4px 12px rgba(31, 117, 94, 0.2)';
    });

    element.addEventListener('mouseup', function(e) {
      if (config.reduceMotion || this.disabled) return;

      this.style.transform = 'translateY(-3px)';
      this.style.boxShadow = '0 8px 24px rgba(31, 117, 94, 0.35)';
    });

    // =====================================================
    // 5. ESTADO DE CARGA (data-loading)
    // =====================================================
    if (element.hasAttribute('data-loading')) {
      element.addEventListener('click', function() {
        if (!config.reduceMotion) {
          this.style.pointerEvents = 'none';
          this.style.opacity = '0.7';
          
          // Guardar texto original
          this.dataset.originalText = this.textContent;
          
          // Mostrar spinner
          const originalHTML = this.innerHTML;
          this.innerHTML = '⏳ Procesando...';
          
          // Restaurar después de 5 segundos (fallback)
          setTimeout(() => {
            this.style.pointerEvents = 'auto';
            this.style.opacity = '1';
            this.innerHTML = originalHTML;
          }, 5000);
        }
      });
    }

    // =====================================================
    // 6. NAVEGACIÓN SUAVE (Solo para enlaces <a>)
    // =====================================================
    if (element.tagName === 'A') {
      element.addEventListener('click', function(e) {
        if (config.reduceMotion || this.classList.contains('no-transition')) return;

        const href = this.getAttribute('href');
        if (!href || href.startsWith('javascript:') || href.startsWith('#')) return;

        // Si es navegación interna
        if (href.startsWith('/') || !href.includes('://')) {
          e.preventDefault();

          const main = document.querySelector('main');
          if (main) {
            main.style.opacity = '0';
            main.style.transition = 'opacity 0.3s ease-out';

            setTimeout(() => {
              window.location.href = href;
            }, 300);
          } else {
            window.location.href = href;
          }
        }
      });
    }
  });

  // =====================================================
  // Agregar animaciones CSS si no existen
  // =====================================================
  if (!document.querySelector('style[data-unified-effects]')) {
    const style = document.createElement('style');
    style.setAttribute('data-unified-effects', 'true');
    style.textContent = `
      /* Ripple effect */
      @keyframes rippleEffect {
        to {
          width: 300px;
          height: 300px;
          opacity: 0;
        }
      }

      /* Button pulse al click */
      @keyframes buttonPulse {
        0% {
          box-shadow: 0 4px 12px rgba(31, 117, 94, 0.2);
        }
        50% {
          box-shadow: 0 8px 24px rgba(31, 117, 94, 0.4);
        }
        100% {
          box-shadow: 0 4px 12px rgba(31, 117, 94, 0.2);
        }
      }

      /* Spinner para loading */
      @keyframes spin {
        to {
          transform: rotateZ(360deg);
        }
      }
    `;
    document.head.appendChild(style);
  }
};

  // =====================================================
  // 6. LINK TRANSITIONS
  // =====================================================

  const initLinkTransitions = () => {
    const links = document.querySelectorAll('a[href]:not([href^="#"]):not([target="_blank"])');

    links.forEach((link) => {
      link.addEventListener('click', function(e) {
        if (config.reduceMotion || this.classList.contains('no-transition')) return;

        const href = this.getAttribute('href');
        if (!href || href.startsWith('javascript:')) return;

        // Si es una navegación interna, agregar transición suave
        if (href.startsWith('/')) {
          e.preventDefault();

          const main = document.querySelector('main');
          if (main) {
            main.style.opacity = '0';
            main.style.transition = 'opacity 0.3s ease-out';

            setTimeout(() => {
              window.location.href = href;
            }, 300);
          } else {
            window.location.href = href;
          }
        }
      });
    });
  };

  // =====================================================
  // 7. SCROLL EFFECTS
  // =====================================================

  const initScrollEffects = () => {
    const scrollElements = document.querySelectorAll('[data-scroll-animate]');

    if (!scrollElements.length) return;

    const scrollObserver = new IntersectionObserver((elements) => {
      elements.forEach((element) => {
        if (element.isIntersecting) {
          element.target.style.animation = 'fadeInUp 0.6s ease-out forwards';
          scrollObserver.unobserve(element.target);
        }
      });
    }, { threshold: 0.1 });

    scrollElements.forEach((el) => scrollObserver.observe(el));
  };

        // Achicar el logo al hacer scroll
    window.onscroll = function() {
        const logo = document.querySelector(".logo-wrapper");
        
        // Detecta si el scroll ha bajado más de 10px
        if (document.body.scrollTop > 10 || document.documentElement.scrollTop > 10) {
            logo.classList.add("shrink");
        } else {
            logo.classList.remove("shrink");
        }
    };

  // =====================================================
  // 8. MANAGE FOCUS PARA ACCESIBILIDAD
  // =====================================================

  const initAccessibility = () => {
    // Mejorar navegación con Tab
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Tab') {
        document.body.classList.add('keyboard-nav');
      }
    });

    document.addEventListener('mousedown', () => {
      document.body.classList.remove('keyboard-nav');
    });

    // Agregar estilos focus-visible si no existen
    if (!document.querySelector('style[data-focus-visible]')) {
      const style = document.createElement('style');
      style.setAttribute('data-focus-visible', 'true');
      style.textContent = `
        body.keyboard-nav button:focus,
        body.keyboard-nav a:focus,
        body.keyboard-nav input:focus,
        body.keyboard-nav select:focus,
        body.keyboard-nav textarea:focus {
          outline: 2px solid var(--color-primary, #1f755e);
          outline-offset: 2px;
        }
      `;
      document.head.appendChild(style);
    }
  };

  // =====================================================
  // 9. RESPONSIVE CONTAINER FIX
  // =====================================================

  const initContainerFix = () => {
    const main = document.querySelector('main.container');
    if (!main) return;

    // Asegurar que main tiene dimensiones correctas
    const ensureMainDimensions = () => {
      const computed = window.getComputedStyle(main);
      const height = computed.height;

      if (height === '0px' || height === 'auto') {
        main.style.minHeight = '100vh';
        main.style.display = 'flex';
        main.style.alignItems = 'center';
        main.style.justifyContent = 'center';
        main.style.width = '100%';
        main.style.boxSizing = 'border-box';
      }
    };

    // Ejecutar en carga y en resize
    ensureMainDimensions();
    window.addEventListener('resize', ensureMainDimensions);
    window.addEventListener('load', ensureMainDimensions);
  };

  // =====================================================
  // 10. PREVENT LAYOUT SHIFT - CARDS
  // =====================================================

  const initCardStability = () => {
    const cards = document.querySelectorAll('[class*="card"], form, .content-box');

    cards.forEach((card) => {
      // Asegurar que las tarjetas tienen altura mínima consistente
      const ensureStability = () => {
        const children = card.querySelectorAll('*');
        children.forEach((child) => {
          // Aplicar flexbox para estabilidad
          if (window.getComputedStyle(child).display === 'block') {
            child.style.boxSizing = 'border-box';
          }
        });
      };

      ensureStability();
      window.addEventListener('resize', ensureStability);
    });
  };

  // =====================================================
  // 11. PERFORMANCE MONITORING
  // =====================================================

  const initPerformanceMonitoring = () => {
    if (!window.performance || !window.performance.mark) return;

    window.performance.mark('page-js-start');

    window.addEventListener('load', () => {
      window.performance.mark('page-js-end');
      window.performance.measure('page-js', 'page-js-start', 'page-js-end');

      if (window.console && window.console.log) {
        const measure = window.performance.getEntriesByName('page-js')[0];
        if (measure) {
          console.log(`📊 Page JS ejecutado en ${measure.duration.toFixed(2)}ms`);
        }
      }
    });
  };

  // =====================================================
  // 12. INICIALIZACIÓN PRINCIPAL
  // =====================================================

  const init = () => {
    // Esperar a que el DOM esté listo
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', initAll);
    } else {
      initAll();
    }
  };

  const initAll = () => {
    // Orden de inicialización
    initContainerFix();           // Fix del main debe ser primero
    initPageAnimations();         // Luego animar elementos
    initFormEnhancements();       // Mejorar formularios
    initUnifiedButtonAndLinkInteractions();  // Fusiona las interaccion de link y botones 
    initScrollEffects();          // Efectos al scroll
    initCardStability();          // Estabilidad de tarjetas
    initAccessibility();          // Accesibilidad
    initPerformanceMonitoring();  // Monitoreo de performance

    // Log de inicialización
    console.log('✅ Page.js inicializado correctamente');
  };

  // Iniciar cuando se carga el script
  init();

  // Exponer API pública para debugging
  window.PageJS = {
    config,
    utils: u,
    reinit: initAll,
  };
})();
