import {
  AnonCredsDidCommCredentialFormatService,
  AnonCredsModule,
  AnonCredsDidCommProofFormatService,
  LegacyIndyDidCommCredentialFormatService,
  LegacyIndyDidCommProofFormatService,
  DidCommCredentialV1Protocol,
  DidCommProofV1Protocol,
} from '@credo-ts/anoncreds'

import {
  IndyVdrAnonCredsRegistry,
  IndyVdrIndyDidResolver,
  IndyVdrModule,
  IndyVdrIndyDidRegistrar,
} from '@credo-ts/indy-vdr'

import { AskarModule } from '@credo-ts/askar'

import {
  DidsModule,
  KeyDidRegistrar,
  KeyDidResolver,
  WebDidResolver,
  Agent,
  DidRepository,
  ConsoleLogger,
  LogLevel,
} from '@credo-ts/core'

import {
  DidCommModule,
  DidCommMediatorPickupStrategy,
  DidCommCredentialEventTypes,
  DidCommProofEventTypes,
  DidCommMimeType,
  DidCommTransportEventTypes,
  DidCommTrustPingEventTypes,
  DidCommDidExchangeState,
  DidCommConnectionEventTypes,
  DidCommBasicMessageEventTypes,
  DidCommCredentialState,
  DidCommProofState,
  DidCommHttpOutboundTransport,
  DidCommWsOutboundTransport,
  DidCommInboundTransport,
} from '@credo-ts/didcomm'

import { anoncreds } from '@hyperledger/anoncreds-nodejs'
import { askarNodeJS } from '@openwallet-foundation/askar-nodejs'
import { indyVdr } from '@hyperledger/indy-vdr-nodejs'
import { agentDependencies } from '@credo-ts/node'

import config from './config.cjs'
import deferred from 'deferred'
import process from 'process'
import readline from 'readline'

/*
  Remap all logging to stderr
*/
class ConsoleError extends ConsoleLogger {
  constructor(...args: ConstructorParameters<typeof ConsoleLogger>) {
      super(...args);
      // Map our log levels to console levels
      (this as any).consoleLogMap = {
          [LogLevel.Test]: 'error',
          [LogLevel.Trace]: 'error',
          [LogLevel.Debug]: 'error',
          [LogLevel.Info]: 'error',
          [LogLevel.Warn]: 'error',
          [LogLevel.Error]: 'error',
          [LogLevel.Fatal]: 'error',
      };
  }
}

const characters =
  'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'


function generateString(length) {
  let result = ''
  const charactersLength = characters.length
  for (let i = 0; i < length; i++) {
    result += characters.charAt(Math.floor(Math.random() * charactersLength))
  }

  return result
}

const initializeAgent = async (withMediation, port, agentConfig = null) => {
  // Simple agent configuration. This sets some basic fields like the wallet
  // configuration and the label. It also sets the mediator invitation url,
  // because this is most likely required in a mobile environment.
  try {
  let mediation_url = config.mediation_url
  let endpoints = ['http://' + config.agent_ip + ':' + port]

  const logLevel = parseInt(process.env.AGENT_LOGGING_LEVEL) || LogLevel.Off

  process.stderr.write('Agent Log Level: ' + parseInt(process.env.AGENT_LOGGING_LEVEL) + '\n')

  if (!agentConfig || agentConfig === null || agentConfig.length === 0) {
    agentConfig = {
      label: generateString(14),
      walletConfig: {
        id:  generateString(32),
        key:  generateString(32),
      },
      autoAcceptConnections: true,
      endpoints: endpoints,
      mediation_url: mediation_url,
      autoAcceptInvitation: true,
      logger: new ConsoleError(logLevel),
      didCommMimeType: DidCommMimeType.V1,
      storage: {
        type: 'sqlite',
        config: { memory: true }, // ephemeral
      },
    }
  }

  const legacyIndyCredentialFormat = new LegacyIndyDidCommCredentialFormatService()
  const legacyIndyProofFormat = new LegacyIndyDidCommProofFormatService()
  const anonCredsCredentialFormatService = new AnonCredsDidCommCredentialFormatService()
  const anonCredsProofFormatService = new AnonCredsDidCommProofFormatService()


  
  let modules = {
    indyVdr: new IndyVdrModule({
      indyVdr,
      networks: [{
        genesisTransactions: config.ledger.genesisTransactions,
        indyNamespace: config.ledger.indyNamespace,
        isProduction: config.ledger.isProduction,
        connectOnStartup: config.ledger.connectOnStartup,
      }],
    }),
    askar: new AskarModule({
      askar: askarNodeJS,
      store: {
        id: agentConfig.walletConfig.id,
        key: agentConfig.walletConfig.key,
        database: {
          type: 'sqlite',
          config: { inMemory: true },
        },
      },
    }),
    // mediator: new MediatorModule({
    //   autoAcceptMediationRequests: true,
    // }),
    anoncreds: new AnonCredsModule({
      registries: [new IndyVdrAnonCredsRegistry()],
      anoncreds
    }),
    didcomm: new DidCommModule({
      connections: {
        autoAcceptConnections: true,
      },
      proofs: true,
      credentials: true,
      mediator: false,
      mediationRecipient: {},
      transports: {
        outbound: [
          new DidCommHttpOutboundTransport(),
          new DidCommWsOutboundTransport(),
        ],
      },
    }),
    dids: new DidsModule({
      registrars: [new IndyVdrIndyDidRegistrar(), new KeyDidRegistrar()],
      resolvers: [new IndyVdrIndyDidResolver(), new KeyDidResolver(), new WebDidResolver()],
    }),
  }

  // configure mediator or endpoints
  if (withMediation) {
    delete agentConfig['endpoints']
  } else {
  }

  // A new instance of an agent is created here
  const agent = new Agent({
    config: agentConfig,
    dependencies: agentDependencies,
    modules: modules
  })
  
  
  
  // Register a simple `WebSocket` outbound transport
  // Register a simple `Http` outbound transport
  if (withMediation) {
    // wait for mediation to be configured
    let timeout = Number(config.verified_timeout_seconds) * 1000

    const TimeDelay = new Promise((resolve, reject) => {
      setTimeout(resolve, timeout, false)
    })

    var def = deferred()

    var onConnectedMediation = async (event) => {
      let mediatorConnection = null
      let interval = 100; 
      for (let i = 0; i < Number(timeout - interval); i++)
      {
        // OutboundWebSocketOpenedEvent occurs before mediation is finalized, so we want to check
        // for the default mediation connection until it is not null or we hit a timeout
        // we sleep a small amount between requests just to be kind to our CPU. 
        await new Promise(r => setTimeout(r, interval))
        mediatorConnection = await agent.didcomm.mediationRecipient.findDefaultMediatorConnection()
        if (mediatorConnection != null) {
          break;
        }
      }
      if (event.payload.connectionId === mediatorConnection?.id) {
        def.resolve(true)
        // we no longer need to listen to the event
        agent.events.off(
          DidCommTransportEventTypes.DidCommOutboundWebSocketOpenedEvent,
          onConnectedMediation
        )
      }
    }

    agent.events.on(
      DidCommTransportEventTypes.DidCommOutboundWebSocketOpenedEvent,
      onConnectedMediation
    )

    // Initialize the agent
    await agent.initialize()

    // Mediation URL can be set via config

    if (config.pickup_strategy === 'pickupv2-live') {
      process.stderr.write('Pickup strategy: pickupv2-live')
      await agent.didcomm.mediationRecipient.initiateMessagePickup(
        undefined,
        DidCommMediatorPickupStrategy.PickUpV2LiveMode
      )
    }

    // wait for ws to be configured
    let value = await Promise.race([TimeDelay, def.promise])

    if (!value) {
      // we no longer need to listen to the event in case of failure
      agent.events.off(
        DidCommTransportEventTypes.DidCommOutboundWebSocketOpenedEvent,
        onConnectedMediation
      )
      throw 'Mediator timeout!'
    }
  } else {

    await agent.initialize()
  }

  return [agent, agentConfig]

  } catch (error) {

    process.stderr.write('******** ERROR Error at initialize agent'+ '\n' + error + '\n')
  }
  
}

const pingMediator = async (agent) => {
  // Find mediator

  // wait for the ping
  let timeout = Number(config.verified_timeout_seconds) * 1000

  const TimeDelay = new Promise((resolve, reject) => {
    setTimeout(resolve, timeout, false)
  })

  var def = deferred()

  var onPingResponse = async (event) => {
    const mediatorConnection =
      await agent.didcomm.mediationRecipient.findDefaultMediatorConnection()
    if (event.payload.connectionRecord.id === mediatorConnection?.id) {
      // we no longer need to listen to the event
      agent.events.off(
        DidCommTrustPingEventTypes.DidCommTrustPingResponseReceivedEvent,
        onPingResponse
      )

      def.resolve(true)
    }
  }

  agent.events.on(
    DidCommTrustPingEventTypes.DidCommTrustPingResponseReceivedEvent,
    onPingResponse
  )

  let mediatorConnection =
    await agent.didcomm.mediationRecipient.findDefaultMediatorConnection()

  if (mediatorConnection) {
    //await agent.connections.acceptResponse(mediatorConnection.id)
    await agent.didcomm.connections.sendPing(mediatorConnection.id, {})
  }

  // wait for ping response
  let value = await Promise.race([TimeDelay, def.promise])

  if (!value) {
    // we no longer need to listen to the event in case of failure
    agent.events.off(
      DidCommTrustPingEventTypes.DidCommTrustPingResponseReceivedEvent,
      onPingResponse
    )
    throw 'Mediator timeout!'
  }
}

let deleteOobRecordById = async (agent, id) => {
  await agent.oob.deleteById(id);
};

let receiveInvitation = async (agent, invitationUrl) => {
  // wait for the connection
  let timeout = Number(config.verified_timeout_seconds) * 1000
  const TimeDelay = new Promise((resolve, reject) => {
    setTimeout(resolve, timeout, false)
  })

  var def = deferred()

  var onConnection = async (event) => {
    {
      let payload = event.payload
      if (
        payload.connectionRecord.state === DidCommDidExchangeState.Completed
      ) {
        // the connection is now ready for usage in other protocols!
        // console.log(`Connection for out-of-band id ${payload.connectionRecord.outOfBandId} completed`)
        // Custom business logic can be included here
        // In this example we can send a basic message to the connection, but
        // anything is possible

        agent.events.off(
          DidCommConnectionEventTypes.DidCommConnectionStateChanged,
          onConnection
        )

        def.resolve(true)
      }
    }
  }

  agent.events.on(
    DidCommConnectionEventTypes.DidCommConnectionStateChanged,
    onConnection
  )

  const { outOfBandRecord } = await agent.oob.receiveInvitationFromUrl(
    invitationUrl
  )

  // wait for connection
  let value = await Promise.race([TimeDelay, def.promise])

  if (!value) {
    // we no longer need to listen to the event in case of failure
    agent.events.off(
      DidCommConnectionEventTypes.DidCommConnectionStateChanged,
      onConnection
    )
    throw 'Connection timeout!'
  }

  return outOfBandRecord
}

let receiveInvitationConnectionDid = async (agent, invitationUrl) => {
  let timeout = Number(config.verified_timeout_seconds) * 1000
  const TimeDelay = new Promise((resolve, reject) => {
    setTimeout(resolve, timeout, false)
  })

  var def = deferred()

  var onConnection = async (event) => {
    {
      let payload = event.payload
      if (
        payload.connectionRecord.state === DidCommDidExchangeState.Completed
      ) {
        agent.events.off(
          DidCommConnectionEventTypes.DidCommConnectionStateChanged,
          onConnection
        )

        def.resolve(true)
      }
    }
  }

  agent.events.on(
    DidCommConnectionEventTypes.DidCommConnectionStateChanged,
    onConnection
  )

  let legacyConnectionDid = undefined;
  let connectionId = undefined;
  let oobRecordId = undefined;
  try {
    // LO: need connection record, not OOB record since we need the connection DID
    const { outOfBandRecord, connectionRecord } = await agent.oob.receiveInvitationFromUrl(
      invitationUrl
    )
    const strRes = JSON.stringify(connectionRecord)
    connectionId = connectionRecord.id;
    oobRecordId = outOfBandRecord.id;

    // LO: retrieve the legacy DID. IAS controller needs that to issue against
    // This code adapted from https://github.com/bcgov/bc-wallet-mobile/blob/main/app/src/helpers/BCIDHelper.ts
    const legacyDidKey = '_internal/legacyDid' // TODO:(from BC Wallet code) Waiting for AFJ export of this.
    const didRepository = agent.dependencyManager.resolve(DidRepository)  
    const dids = await didRepository.getAll(agent.context)
    const didRecord = dids.filter((d) => d.did === connectionRecord?.did).pop()
    legacyConnectionDid = didRecord.metadata.get(legacyDidKey)!.unqualifiedDid
  } catch (error) {
    process.stderr.write('******** ERROR'+ '\n' + error + '\n')
  }

  // wait for connection
  let value = await Promise.race([TimeDelay, def.promise])

  if (!value) {
    // we no longer need to listen to the event in case of failure
    agent.events.off(
      DidCommConnectionEventTypes.DidCommConnectionStateChanged,
      onConnection
    )
    throw 'Connection timeout!'
  }

  return { did: legacyConnectionDid, connectionId: connectionId, oobRecordId: oobRecordId}
}

let receiveCredential = async (agent) => {
  // wait for the ping
  let timeout = Number(config.verified_timeout_seconds) * 1000

  const TimeDelay = new Promise((resolve, reject) => {
    setTimeout(resolve, timeout, false)
  })

  var def = deferred()

  let onCredential = async (event) => {
    let payload = event.payload

    switch (payload.credentialRecord.state) {
      case DidCommCredentialState.OfferReceived:
        // custom logic here
        await agent.didcomm.credentials.acceptOffer({
          credentialRecordId: payload.credentialRecord.id,
        })
        break
      case DidCommCredentialState.CredentialReceived:
        // For demo purposes we exit the program here.

        agent.events.off(
          DidCommCredentialEventTypes.DidCommCredentialStateChanged,
          onCredential
        )

        def.resolve(true)
        break
    }
  }

  agent.events.on(
    DidCommCredentialEventTypes.DidCommCredentialStateChanged,
    onCredential
  )

  // Nothing for us to do

  // wait for credential
  let value = await Promise.race([TimeDelay, def.promise])

  if (!value) {
    // we no longer need to listen to the event in case of failure
    agent.events.off(
      DidCommCredentialEventTypes.DidCommCredentialStateChanged,
      onCredential
    )
    throw 'Credential timeout!'
  }
}

let presentationExchange = async (agent) => {
  // wait for the ping
  let timeout = Number(config.verified_timeout_seconds) * 1000

  const TimeDelay = new Promise((resolve, reject) => {
    setTimeout(resolve, timeout, false)
  })

  var def = deferred()

  let onRequest = async (event) => {
    let payload = event.payload

    switch (payload.proofRecord.state) {
      case DidCommProofState.RequestReceived:
        const requestedCredentials =
          await agent.didcomm.proofs.selectCredentialsForRequest({
            proofRecordId: payload.proofRecord.id,
            // config: {
            //   filterByPresentationPreview: true,
            // },
          })
        await agent.didcomm.proofs.acceptRequest({
          proofRecordId: payload.proofRecord.id,
          proofFormats: requestedCredentials.proofFormats,
        })
        agent.events.off(DidCommProofEventTypes.ProofStateChanged, onRequest)
        def.resolve(true)
        break
    }
  }

  agent.events.on(DidCommProofEventTypes.ProofStateChanged, onRequest)

  // Wait for presentation
  let value = await Promise.race([TimeDelay, def.promise])

  if (!value) {
    // No longer need to listen to the event in case of failure
    agent.events.off(DidCommProofEventTypes.ProofStateChanged, onRequest)
    throw 'Presentation timeout!'
  }
}

let receiveMessage = async (agent) => {
  // wait for the ping
  let timeout = Number(config.verified_timeout_seconds) * 1000

  const TimeDelay = new Promise((resolve, reject) => {
    setTimeout(resolve, timeout, false)
  })

  var def = deferred()

  let onMessage = async (event) => {
    let payload = event.payload

    //        console.error(payload)

    agent.events.off(
      DidCommBasicMessageEventTypes.DidCommBasicMessageStateChanged,
      onMessage
    )

    def.resolve(true)
  }

  agent.events.on(
    DidCommBasicMessageEventTypes.DidCommBasicMessageStateChanged,
    onMessage
  )

  // Nothing for us to do

  // wait for credential
  let value = await Promise.race([TimeDelay, def.promise])

  if (!value) {
    // we no longer need to listen to the event in case of failure
    agent.events.off(
      DidCommBasicMessageEventTypes.DidCommBasicMessageStateChanged,
      onMessage
    )
    throw 'Message timeout!'
  }
}

// var readline = require('readline')

var rl = readline.createInterface(process.stdin, null)

var agent = null
var agentConfig = null

rl.setPrompt('')
rl.prompt(false)

const handleError = async (e) => {
  process.stdout.write(JSON.stringify({ error: 1, result: e }) + '\n')
}

rl.on('line', async (line) => {
  try {
    var command = JSON.parse(line)
    // console.log('command: ',command);
    if (command['cmd'] == 'start') {
      [agent, agentConfig] = await initializeAgent(
        command['withMediation'],
        command['port'],
        command['agentConfig']
      )
      // if (command["agentConfig"] === null || !command["agentConfig"]) {
      //   [agent, agentConfig] = await initializeAgent(
      //     command["withMediation"],
      //     command["port"]
      //   );
      // } else {
      //   [agent, agentConfig] = await initializeAgent();
      // }
      // process.stdout.write(
      //   JSON.stringify({ error: 0, result: "Initialized agent..." }) + "\n"
      // );
      process.stdout.write(
        JSON.stringify({ error: 0, result: agentConfig }) + '\n'
      )
    } else if (command['cmd'] == 'ping_mediator') {
      await pingMediator(agent)
      process.stdout.write(
        JSON.stringify({ error: 0, result: 'Ping Mediator' }) + '\n'
      )
    } else if (command['cmd'] == 'deleteOobRecordById') {
      await deleteOobRecordById(agent, command['id'])

      process.stdout.write(
        JSON.stringify({ error: 0, result: 'Delete OOB Record' }) + '\n'
      )
    } else if (command['cmd'] == 'receiveInvitation') {
      let connection = await receiveInvitation(agent, command['invitationUrl'])

      process.stdout.write(
        JSON.stringify({
          error: 0,
          result: 'Receive Connection',
          connection: connection,
        }) + '\n'
      )
    } else if (command['cmd'] == 'receiveInvitationConnectionDid') {
      let connection = await receiveInvitationConnectionDid(agent, command['invitationUrl'])

      process.stdout.write(
        JSON.stringify({
          error: 0,
          result: 'Receive Invitation Connection',
          connection: connection,
        }) + '\n'
      )
    } else if (command['cmd'] == 'receiveCredential') {
      await receiveCredential(agent)

      process.stdout.write(
        JSON.stringify({ error: 0, result: 'Receive Credential' }) + '\n'
      )
    } else if (command['cmd'] == 'presentationExchange') {
      await presentationExchange(agent)

      process.stdout.write(
        JSON.stringify({ error: 0, result: 'Presentation Exchange' }) + '\n'
      )
    } else if (command['cmd'] == 'receiveMessage') {
      await receiveMessage(agent)

      process.stdout.write(
        JSON.stringify({ error: 0, result: 'Receive Message' }) + '\n'
      )
    } else if (command['cmd'] == 'shutdown') {
      process.stdout.write(
        JSON.stringify({ error: 0, result: 'Shutting down agent' }) + '\n'
      )
      rl.close()
      await agent.shutdown()
      process.exit(1)
    } else {
      handleError('Invalid command')
    }
  } catch (e) {
    if (e.name === 'JSONDecodeError') {
      process.stdout.write(
        JSON.stringify({ error: 0, result: 'JSONDecodeError received' }) + '\n'
      )
    }
    handleError(e)
  }
})

process.once('SIGTERM', function (code) {
  process.stderr.write('SIGTERM received...' + '\n')
  process.exit(1)
})
