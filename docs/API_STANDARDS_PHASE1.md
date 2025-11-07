# API Response Standards - Phase 1

##  JSON Response Conventions

###  **Standard Error Format**
```json
{
  "error": "Error message in English",
  "details": "Additional details (optional)",
  "type": "error_type_snake_case",
  "retry_suggestion": "User-friendly retry instruction (optional)"
}
```

###  **Standard Success Format**
```json
{
  "message": "Success message in English",
  "data": { /* relevant data */ },
  "additional_info": { /* optional extra data */ }
}
```

##  **Field Naming Conventions**

### **Consistent Fields (English):**
-  `error` (not `erro`)
-  `message` (not `mensagem`)
-  `details` (not `detalhes`)
-  `type` (not `tipo`)
-  `retry_suggestion` (not `retry_sugestao`)
-  `contact_support` (not `contato_suporte`)
-  `active` (not `ativo`)
-  `period_days` (not `periodo_dias`)

### **Trade Protection Fields:**
```json
{
  "trade_protection": {
    "active": true,
    "period_days": 7,
    "message": "Protection message",
    "hold_info": { /* hold details */ }
  }
}
```

##  **HTTP Status Codes**

- `200` - Success
- `400` - Bad Request (validation errors)
- `401` - Unauthorized (authentication required)
- `403` - Forbidden (permission denied)
- `404` - Not Found
- `429` - Too Many Requests (rate limiting)
- `500` - Internal Server Error
- `502` - Bad Gateway (network issues)
- `503` - Service Unavailable (Steam issues)
- `504` - Gateway Timeout

##  **Frontend Integration**

### **JavaScript Error Handling:**
```javascript
.then(response => response.json())
.then(data => {
    if (data.error) {
        // Handle error
        showError(data.error, data.details);
    } else if (data.message) {
        // Handle success
        showSuccess(data.message);
    }
});
```

### **Required Frontend Updates:**
-  `data.error` instead of `data.erro`
-  `data.message` instead of `data.mensagem`
-  `data.trade_protection.message` instead of `data.trade_protection.mensagem`
-  `data.trade_protection.active` instead of `data.trade_protection.ativo`

##  **Implementation Status**

###  **Phase 1 Completed:**
- [x] `/trade/enviar-oferta` - All responses standardized
- [x] `/saque` - Error responses standardized
- [x] `dashboard-updated.js` - Updated to handle new format
- [x] Error handling consistency across routes

###  **Next Steps (Future Phases):**
- [ ] Function names in English
- [ ] Endpoint names in English
- [ ] Database model names in English
- [ ] Complete frontend localization

##  **Breaking Changes**

**Frontend must be updated to handle:**
1. `error` field instead of `erro`
2. `message` field instead of `mensagem`
3. New trade_protection field names

**Backward Compatibility:**
- None required for Phase 1
- All changes are consistent and applied simultaneously

##  **Testing Checklist**

- [ ] Error responses display correctly
- [ ] Success messages work
- [ ] Trade protection info shows properly
- [ ] Rate limiting messages are clear
- [ ] Steam error handling is user-friendly

---

**Last Updated:** July 31, 2025  
**Phase:** 1 - JSON Response Standardization  
**Status:**  Complete
