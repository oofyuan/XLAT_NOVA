#ifndef GFX_I18N_H
#define GFX_I18N_H

typedef enum {
    GFX_LANG_EN = 0,
    GFX_LANG_ZH = 1,
} gfx_lang_t;

void gfx_i18n_init(gfx_lang_t lang);
gfx_lang_t gfx_i18n_lang_get(void);
void gfx_i18n_lang_set(gfx_lang_t lang);
const char *gfx_i18n_tr(const char *en, const char *zh);

#endif
