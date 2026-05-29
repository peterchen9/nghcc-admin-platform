# Database Schema 盤點

更新日期：2026-05-29

## 資料庫摘要

| 項目 | 數量 |
| --- | ---: |
| Database | `nghcc_admin` |
| Tables | 52 |
| Users | 5 |
| Menu items | 23 |
| Active menu items | 22 |
| Django permissions | 185 |
| User permission grants | 326 |
| Group permission grants | 161 |
| Menu permission grants | 44 |
| Auth groups | 1 |

## 主要資料表

| 資料表 | 用途 | 估計筆數 |
| --- | --- | ---: |
| `auth_user` | Django 使用者 | 5 |
| `auth_permission` | Django 權限定義 | 185 |
| `auth_user_user_permissions` | 使用者直接權限 | 326 |
| `auth_group_permissions` | 群組權限 | 161 |
| `accounts_userprofile` | 使用者延伸資料 | 5 |
| `accounts_userprofile_allowed_menu_items` | 使用者可見選單 | 44 |
| `menu_menuitem` | 左側功能選單 | 23 |
| `members` | 會員與新朋友資料 | 7414 |
| `checkin_records` | 報到或聚會紀錄 | 107328 |
| `hymns` | 詩歌資料庫 | 2841 |
| `accounts_systemsetting` | 系統設定 | 3 |
| `django_session` | Django session | 21 |
| `django_admin_log` | Django admin 操作記錄 | 20 |

## CMS / Filer 相關表

正式資料庫仍包含 Django CMS、filer、easy-thumbnails、djangocms-text-ckeditor 等表，多數目前為 0 筆：

| 類型 | 代表資料表 | 目前狀態 |
| --- | --- | --- |
| Django CMS | `cms_page`, `cms_placeholder`, `cms_cmsplugin` | 多數 0 筆 |
| Filer | `filer_file`, `filer_folder`, `filer_image` | 多數 0 筆 |
| Easy thumbnails | `easy_thumbnails_source`, `easy_thumbnails_thumbnail` | 多數 0 筆 |
| Versioning | `djangocms_versioning_version` | 0 筆 |

這些表可能是舊版 CMS 嘗試或套件依賴殘留，後續可評估是否仍需保留。

## Django Model 對應

| App | Model | DB table | 備註 |
| --- | --- | --- | --- |
| `accounts` | `UserProfile` | `accounts_userprofile` | 使用者延伸資料、選單權限 |
| `accounts` | `SystemSetting` | `accounts_systemsetting` | 系統設定 |
| `menu` | `MenuItem` | `menu_menuitem` | 左側選單 |
| `pages` | `Page` | `pages_page` | 首頁與內容頁，正式目前 0 筆 |
| `eureka` | `Member` | `members` | `managed = False` |
| `hymns` | `Hymn` | `hymns` | `managed = False` |

## Schema 管理注意事項

1. `members` 與 `hymns` 是正式資料核心表，但 Django model 設為 `managed = False`，代表 migration 不會管理 schema。
2. `checkin_records` 有大量資料，但目前程式沒有完整 model 與 UI 對應，需補建資料模型或清楚定義來源。
3. `pages_page` 目前 0 筆，但首頁仍可顯示，代表首頁可能依系統設定或 fallback template 運作。
4. CMS 相關資料表數量多但資料少，需確認是否仍為必要套件，避免升級與維護成本。
5. 權限由 Django permission、user direct permissions、group permissions、menu permissions 混合構成，需整理為一致模型。

## 角色與權限統計

目前正式資料還原後的權限資料可分為：

| 權限類型 | 數量 |
| --- | ---: |
| Django permission definitions | 185 |
| 使用者直接權限關聯 | 326 |
| 群組權限關聯 | 161 |
| 選單可見權限關聯 | 44 |
| 群組數量 | 1 |

若以「權限定義」計算，權限數量為 185。若以「實際授權關聯」計算，授權關聯為 531。若把權限定義與授權關聯合併統計，總數為 716。
