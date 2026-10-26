# Packet Tracer – Filiais Madrid, Barcelona e Valência

## 5.1 Mapa de endereços

Regra: escolher a menor sub-rede em que `2^n - 2` (hosts úteis) cabe a demanda.

| Filial | Rede original | Demanda | Hosts úteis | Prefixo | Máscara | Sub-rede | 1º IP (gateway) | Último IP | Broadcast |
|---|---|---|---|---|---|---|---|---|---|
| Madrid (Router0) | 192.168.0.0 | 58 | 62 (2^6 - 2) | /26 | 255.255.255.192 | 192.168.0.0/26 | 192.168.0.1 | 192.168.0.62 | 192.168.0.63 |
| Barcelona (Router1) | 172.16.0.0 | 15 | 30 (2^5 - 2) | /27 | 255.255.255.224 | 172.16.0.0/27 | 172.16.0.1 | 172.16.0.30 | 172.16.0.31 |
| Valência (Router2) | 10.0.0.0 | 28 | 30 (2^5 - 2) | /27 | 255.255.255.224 | 10.0.0.0/27 | 10.0.0.1 | 10.0.0.30 | 10.0.0.31 |

Por que não menor: /27 em Madrid só dá 30 hosts (< 58); /28 em Barcelona só dá 14 (< 15).

## Links seriais entre roteadores (cabos vermelhos)

O enunciado não define esses IPs. Se o professor passou outros, use os dele.

| Link | Rede | Lado A | Lado B |
|---|---|---|---|
| Router0 ↔ Router1 | 192.168.1.0/30 (255.255.255.252) | Router0 = 192.168.1.1 | Router1 = 192.168.1.2 |
| Router0 ↔ Router2 | 192.168.2.0/30 (255.255.255.252) | Router0 = 192.168.2.1 | Router2 = 192.168.2.2 |
| Router1 ↔ Router2 | 192.168.3.0/30 (255.255.255.252) | Router1 = 192.168.3.1 | Router2 = 192.168.3.2 |

## Antes de configurar: descobrir o nome das portas

`Options > Preferences > Interface` → marcar **Always Show Port Labels in Logical Workspace**.

Os scripts abaixo supõem:

- cabo para o switch = `FastEthernet0/0`
- Router0: `Serial0/0/0` → Router1, `Serial0/0/1` → Router2
- Router1: `Serial0/0/0` → Router0, `Serial0/0/1` → Router2
- Router2: `Serial0/0/0` → Router0, `Serial0/0/1` → Router1

Se no seu desenho estiver diferente, troque o nome da interface no script.

## Configuração (aba CLI de cada roteador)

Se aparecer `Would you like to enter the initial configuration dialog? [yes/no]:`, digite `no` e Enter.
Dá para colar o bloco inteiro de uma vez na aba CLI.

`clock rate 64000` só vale no lado DCE do cabo serial; no lado DTE o roteador avisa que não se aplica e ignora, então pode deixar nos dois.

### Router0 – Madrid

```
enable
configure terminal
interface FastEthernet0/0
 ip address 192.168.0.1 255.255.255.192
 no shutdown
 exit
interface Serial0/0/0
 ip address 192.168.1.1 255.255.255.252
 clock rate 64000
 no shutdown
 exit
interface Serial0/0/1
 ip address 192.168.2.1 255.255.255.252
 clock rate 64000
 no shutdown
 exit
router rip
 version 2
 no auto-summary
 network 192.168.0.0
 network 192.168.1.0
 network 192.168.2.0
 exit
end
write
```

### Router1 – Barcelona

```
enable
configure terminal
interface FastEthernet0/0
 ip address 172.16.0.1 255.255.255.224
 no shutdown
 exit
interface Serial0/0/0
 ip address 192.168.1.2 255.255.255.252
 clock rate 64000
 no shutdown
 exit
interface Serial0/0/1
 ip address 192.168.3.1 255.255.255.252
 clock rate 64000
 no shutdown
 exit
router rip
 version 2
 no auto-summary
 network 172.16.0.0
 network 192.168.1.0
 network 192.168.3.0
 exit
end
write
```

### Router2 – Valência

```
enable
configure terminal
interface FastEthernet0/0
 ip address 10.0.0.1 255.255.255.224
 no shutdown
 exit
interface Serial0/0/0
 ip address 192.168.2.2 255.255.255.252
 clock rate 64000
 no shutdown
 exit
interface Serial0/0/1
 ip address 192.168.3.2 255.255.255.252
 clock rate 64000
 no shutdown
 exit
router rip
 version 2
 no auto-summary
 network 10.0.0.0
 network 192.168.2.0
 network 192.168.3.0
 exit
end
write
```

## Alternativa sem comandos (aba Config)

Clicar no roteador → aba **Config** → na lista da esquerda, `FastEthernet0/0` ou `Serial0/0/x`:

1. **Port Status**: marcar **On**
2. **IPv4 Address** e **Subnet Mask**: preencher conforme as tabelas
3. Na serial, se aparecer **Clock Rate**, escolher `64000`

Roteamento sem comandos: na mesma aba Config, `Routing > RIP` → em **Network** digitar cada rede ligada ao roteador (as mesmas dos comandos `network` acima) e clicar **Add**. Esse menu cria RIP versão 1, que funciona nesta topologia porque cada filial e cada link serial estão numa rede classful diferente.

## Testar com PCs (opcional)

Arraste um PC (End Devices) para cada switch e ligue com cabo **Copper Straight-Through** (linha preta contínua).
No PC: **Desktop > IP Configuration** → Static:

| PC | IP | Máscara | Default Gateway |
|---|---|---|---|
| PC Madrid | 192.168.0.10 | 255.255.255.192 | 192.168.0.1 |
| PC Barcelona | 172.16.0.10 | 255.255.255.224 | 172.16.0.1 |
| PC Valência | 10.0.0.10 | 255.255.255.224 | 10.0.0.1 |

Depois, em **Desktop > Command Prompt** do PC Madrid: `ping 172.16.0.10` e `ping 10.0.0.10`.
O primeiro ping pode perder 1–2 pacotes (ARP); repita.

## Verificação no roteador

```
show ip interface brief
show ip route
```

- `show ip interface brief`: todas as interfaces usadas com `up  up`.
- `show ip route`: linhas com `R` (aprendidas por RIP) para as redes das outras filiais.
- Serial `down`: verificar `no shutdown` nos dois roteadores e o `clock rate` no lado DCE (`show controllers Serial0/0/0` mostra se é DCE ou DTE).

Por fim, salvar o arquivo .pkt (Ctrl+S).
