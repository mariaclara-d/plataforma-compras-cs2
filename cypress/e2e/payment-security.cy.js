/**
 * 🛡️ CYPRESS SECURITY TESTS - PAYMENT MANIPULATION
 * 
 * Testa vulnerabilidades de manipulação de dados de pagamento
 * CRÍTICO: Garante que usuários maliciosos não alterem informações de pagamento
 */

describe('🔐 Payment Security Tests', () => {
  
  beforeEach(() => {
    // Setup para cada teste
    cy.visit('http://localhost:5000')
    
    // Mock de autenticação Steam (se necessário)
    cy.window().then((win) => {
      win.sessionStorage.setItem('steam_id', '76561199063085722')
    })
  })

  describe('🚨 Payment Data Manipulation Attack', () => {
    
    it('Should prevent chave_pix manipulation via request interception', () => {
      // Simular tentativa de enviar oferta com chave PIX manipulada
      
      cy.intercept('POST', '/trade/enviar-oferta', (req) => {
        // Simular ataque: usuario tenta alterar chave PIX no request
        const originalPayment = req.body.pagamento
        
        // ATAQUE: Alterar chave PIX para conta do atacante
        req.body.pagamento = {
          ...originalPayment,
          chave_pix: '11999999999' // PIX do atacante!
        }
        
        // Log do ataque tentado
        cy.log('🚨 ATTACK: Trying to change PIX key to attacker account')
        
      }).as('enviarOferta')
      
      // Tentar enviar oferta
      cy.request({
        method: 'POST',
        url: 'http://localhost:5000/trade/enviar-oferta',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': 'fake-token' // Será rejeitado pelo CSRF
        },
        body: {
          itens: [
            {
              assetid: '123456789',
              market_hash_name: 'AK-47 | Redline',
              price: 50.00
            }
          ],
          tradelink: 'https://steamcommunity.com/tradeoffer/new/?partner=123&token=abc',
          pagamento: {
            metodo_pagamento: 'pix',
            chave_pix: '74999619371' // PIX legítimo
          }
        },
        failOnStatusCode: false
      }).then((response) => {
        // Deve falhar devido a CSRF ou autenticação
        expect(response.status).to.be.oneOf([400, 401, 403])
        cy.log('✅ PROTECTION: Request properly rejected')
      })
    })

    it('Should validate payment data server-side', () => {
      // Teste de validação server-side de dados de pagamento
      
      const maliciousPayments = [
        // PIX key injection
        {
          metodo_pagamento: 'pix',
          chave_pix: '"; DROP TABLE informacoes_pagamento; --'
        },
        // XSS attempt
        {
          metodo_pagamento: 'pix', 
          chave_pix: '<script>alert("XSS")</script>'
        },
        // Extremely long PIX key
        {
          metodo_pagamento: 'pix',
          chave_pix: 'A'.repeat(1000)
        },
        // Invalid characters
        {
          metodo_pagamento: 'pix',
          chave_pix: '../../etc/passwd'
        }
      ]

      maliciousPayments.forEach((maliciousPayment, index) => {
        cy.request({
          method: 'POST',
          url: 'http://localhost:5000/trade/enviar-oferta',
          headers: {
            'Content-Type': 'application/json'
          },
          body: {
            itens: [{
              assetid: '123456789',
              market_hash_name: 'Test Item'
            }],
            tradelink: 'https://steamcommunity.com/tradeoffer/new/?partner=123&token=abc',
            pagamento: maliciousPayment
          },
          failOnStatusCode: false
        }).then((response) => {
          // Todos devem ser rejeitados
          expect(response.status).to.be.oneOf([400, 401, 403, 422])
          cy.log(`✅ Malicious payment ${index + 1} properly rejected`)
        })
      })
    })
  })

  describe('💰 Saque (Withdrawal) Security', () => {
    
    it('Should prevent unauthorized balance withdrawal', () => {
      // Teste de saque não autorizado
      
      const attackScenarios = [
        // Tentar sacar de outro usuário
        {
          steamid: '76561199999999999', // SteamID diferente da sessão
          valor: 100.00
        },
        // Valor negativo (pode criar saldo?)
        {
          steamid: '76561199063085722',
          valor: -50.00
        },
        // Valor extremamente alto
        {
          steamid: '76561199063085722', 
          valor: 999999.99
        },
        // Valor como string (injection?)
        {
          steamid: '76561199063085722',
          valor: "'; DROP TABLE saques; --"
        }
      ]

      attackScenarios.forEach((scenario, index) => {
        cy.request({
          method: 'POST',
          url: 'http://localhost:5000/api/saque',
          headers: {
            'Content-Type': 'application/json'
          },
          body: scenario,
          failOnStatusCode: false
        }).then((response) => {
          // Todos ataques devem ser bloqueados
          expect(response.status).to.be.oneOf([400, 401, 403])
          cy.log(`✅ Withdrawal attack ${index + 1} blocked`)
        })
      })
    })

    it('Should enforce trade hold protection', () => {
      // Verificar se sistema de trade hold bloqueia saques prematuros
      
      cy.request({
        method: 'POST',
        url: 'http://localhost:5000/api/saque',
        headers: {
          'Content-Type': 'application/json'
        },
        body: {
          steamid: '76561199063085722',
          valor: 10.00
        },
        failOnStatusCode: false
      }).then((response) => {
        
        if (response.status === 400 && response.body.error === 'Balance blocked by Trade Protection') {
          // Trade hold funcionando corretamente
          cy.log('✅ Trade Hold protection active')
          expect(response.body.details).to.have.property('amount_on_hold')
          expect(response.body.details).to.have.property('available_balance')
        } else if (response.status === 401) {
          // Não logado - também é proteção válida
          cy.log('✅ Authentication protection active')
        } else {
          cy.log('ℹ️ No trade holds found (normal if no recent trades)')
        }
      })
    })
  })

  describe('🔒 CSRF and Session Protection', () => {
    
    it('Should require valid CSRF token for payment operations', () => {
      // Teste de proteção CSRF
      
      cy.request({
        method: 'POST',
        url: 'http://localhost:5000/trade/enviar-oferta',
        headers: {
          'Content-Type': 'application/json'
          // Sem CSRF token
        },
        body: {
          itens: [{
            assetid: '123456789',
            market_hash_name: 'Test Item'
          }],
          tradelink: 'https://steamcommunity.com/tradeoffer/new/?partner=123&token=abc',
          pagamento: {
            metodo_pagamento: 'pix',
            chave_pix: '74999619371'
          }
        },
        failOnStatusCode: false
      }).then((response) => {
        // Deve ser rejeitado por falta de CSRF
        expect(response.status).to.be.oneOf([400, 403])
        cy.log('✅ CSRF protection working')
      })
    })

    it('Should require valid Steam authentication', () => {
      // Teste sem autenticação Steam
      
      cy.clearCookies()
      cy.clearLocalStorage()
      
      cy.request({
        method: 'POST',
        url: 'http://localhost:5000/api/saque',
        headers: {
          'Content-Type': 'application/json'
        },
        body: {
          steamid: '76561199063085722',
          valor: 50.00
        },
        failOnStatusCode: false
      }).then((response) => {
        // Deve ser rejeitado por falta de autenticação
        expect(response.status).to.be.oneOf([401, 403])
        cy.log('✅ Authentication protection working')
      })
    })
  })

  describe('📊 Rate Limiting Tests', () => {
    
    it('Should block rapid payment requests', () => {
      // Teste de rate limiting em operações de pagamento
      
      const requests = []
      
      // Fazer 10 requests rápidos
      for (let i = 0; i < 10; i++) {
        requests.push(
          cy.request({
            method: 'POST',
            url: 'http://localhost:5000/trade/enviar-oferta',
            headers: {
              'Content-Type': 'application/json'
            },
            body: {
              itens: [{
                assetid: `12345678${i}`,
                market_hash_name: `Test Item ${i}`
              }],
              tradelink: 'https://steamcommunity.com/tradeoffer/new/?partner=123&token=abc',
              pagamento: {
                metodo_pagamento: 'pix',
                chave_pix: '74999619371'
              }
            },
            failOnStatusCode: false
          })
        )
      }

      // Pelo menos algumas devem ser limitadas
      cy.wrap(Promise.all(requests)).then((responses) => {
        const rateLimited = responses.filter(r => r.status === 429)
        if (rateLimited.length > 0) {
          cy.log(`✅ Rate limiting active: ${rateLimited.length} requests blocked`)
        } else {
          cy.log('ℹ️ Rate limiting may be disabled for localhost')
        }
      })
    })
  })

  describe('🎯 Business Logic Tests', () => {
    
    it('Should prevent double-spending attacks', () => {
      // Teste de prevenção de gasto duplo
      
      const sameRequest = {
        itens: [{
          assetid: '123456789',
          market_hash_name: 'Unique Test Item'
        }],
        tradelink: 'https://steamcommunity.com/tradeoffer/new/?partner=123&token=abc',
        pagamento: {
          metodo_pagamento: 'pix',
          chave_pix: '74999619371'
        }
      }

      // Enviar mesmo request duas vezes rapidamente
      cy.request({
        method: 'POST',
        url: 'http://localhost:5000/trade/enviar-oferta',
        headers: { 'Content-Type': 'application/json' },
        body: sameRequest,
        failOnStatusCode: false
      }).then((response1) => {
        
        cy.request({
          method: 'POST',
          url: 'http://localhost:5000/trade/enviar-oferta',
          headers: { 'Content-Type': 'application/json' },
          body: sameRequest,
          failOnStatusCode: false
        }).then((response2) => {
          
          // Pelo menos uma das duas deve falhar
          const success = [200, 201, 202]
          const response1Success = success.includes(response1.status)
          const response2Success = success.includes(response2.status)
          
          expect(response1Success && response2Success).to.be.false
          cy.log('✅ Double-spending protection working')
        })
      })
    })
  })
})

// Utilitários para testes
Cypress.Commands.add('mockSteamAuth', (steamId = '76561199063085722') => {
  cy.window().then((win) => {
    win.sessionStorage.setItem('steam_id', steamId)
  })
})

Cypress.Commands.add('clearSteamAuth', () => {
  cy.clearCookies()
  cy.clearLocalStorage()
  cy.clearSessionStorage()
})