#include "settings_store.h"

#include "stm32f7xx_hal.h"
#include "stm32f7xx_hal_flash.h"
#include "stm32f7xx_hal_flash_ex.h"

/*
 * Reserve the last internal Flash sector for a tiny settings area.
 * The linker script keeps the application below 0x080C0000.
 */
#define SETTINGS_FLASH_ADDR       0x080C0000UL
#define SETTINGS_FLASH_SECTOR     FLASH_SECTOR_7
#define SETTINGS_MAGIC            0x584C4154UL /* "XLAT" */
#define SETTINGS_LANG_ADDR        (SETTINGS_FLASH_ADDR + 4UL)
#define SETTINGS_VERSION_ADDR     (SETTINGS_FLASH_ADDR + 8UL)

/*
 * djb2-style hash of the firmware version string.
 * Used to detect a firmware upgrade: when the version changes, the
 * persisted settings (e.g. language) are reset to their defaults.
 */
static uint32_t version_hash(const char *s)
{
    uint32_t h = 5381;
    if (s == NULL) {
        return 0;
    }
    while (*s) {
        h = h * 33u + (uint8_t)(*s++);
    }
    return h;
}

static uint32_t current_version_hash(void)
{
    return version_hash(APP_VERSION_FULL);
}

static void settings_store_write(gfx_lang_t lang)
{
    FLASH_EraseInitTypeDef erase;
    uint32_t sector_error = 0;
    HAL_StatusTypeDef status;

    erase.TypeErase = FLASH_TYPEERASE_SECTORS;
    erase.Sector = SETTINGS_FLASH_SECTOR;
    erase.NbSectors = 1;
    erase.VoltageRange = FLASH_VOLTAGE_RANGE_3;

    HAL_FLASH_Unlock();
    __HAL_FLASH_CLEAR_FLAG(FLASH_FLAG_EOP | FLASH_FLAG_OPERR | FLASH_FLAG_WRPERR |
                           FLASH_FLAG_PGAERR | FLASH_FLAG_PGPERR | FLASH_FLAG_ERSERR);

    status = HAL_FLASHEx_Erase(&erase, &sector_error);
    if (status == HAL_OK) {
        (void)HAL_FLASH_Program(FLASH_TYPEPROGRAM_WORD, SETTINGS_FLASH_ADDR,
                                SETTINGS_MAGIC);
        (void)HAL_FLASH_Program(FLASH_TYPEPROGRAM_WORD, SETTINGS_LANG_ADDR,
                                (uint32_t)lang);
        (void)HAL_FLASH_Program(FLASH_TYPEPROGRAM_WORD, SETTINGS_VERSION_ADDR,
                                current_version_hash());
    }

    HAL_FLASH_Lock();
}

void settings_store_init(void)
{
    gfx_lang_t lang = GFX_LANG_EN;

    uint32_t magic = *(volatile uint32_t *)SETTINGS_FLASH_ADDR;
    uint32_t lang_raw = *(volatile uint32_t *)SETTINGS_LANG_ADDR;
    uint32_t stored_ver = *(volatile uint32_t *)SETTINGS_VERSION_ADDR;

    if (magic == SETTINGS_MAGIC) {
        if ((lang_raw == GFX_LANG_EN || lang_raw == GFX_LANG_ZH) &&
            (stored_ver == current_version_hash())) {
            /* Settings belong to this firmware version: keep them. */
            lang = (gfx_lang_t)lang_raw;
        } else {
            /*
             * Settings were written by an older firmware (no version field)
             * or by a different firmware version: reset to the default
             * language and persist the new version.
             */
            lang = GFX_LANG_EN;
            settings_store_write(GFX_LANG_EN);
        }
    }

    gfx_i18n_init(lang);
}

void settings_store_save_language(gfx_lang_t lang)
{
    if ((lang != GFX_LANG_EN) && (lang != GFX_LANG_ZH)) {
        return;
    }
    settings_store_write(lang);
}
