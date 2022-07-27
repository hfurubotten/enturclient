"""GraphQL query templates."""

GRAPHQL_STOP_TO_QUAY_QUERY = """
query(
    $stops: [String]!,
    $whitelist: InputWhiteListed,
    $omitNonBoarding: Boolean = true){
  stopPlaces(ids: $stops) {
    id
    quays(filterByInUse: true){
      id
      estimatedCalls(
          timeRange: 172100,
          numberOfDepartures: 1,
          whiteListed: $whitelist,
          omitNonBoarding: $omitNonBoarding){
        destinationDisplay {
          frontText
        }
      }
    }
  }
}
"""
GRAPHQL_STOP_TEMPLATE = """
  stopPlaces(ids: $stops) {
    id
    name
    estimatedCalls(
        whiteListed: $whitelist,
        numberOfDepartures: $numberOfDepartures) {
      ...callData
    }
  }
"""
GRAPHQL_QUAY_TEMPLATE = """
  quays(ids: $quays) {
    id
    name
    publicCode
    latitude
    longitude
    estimatedCalls(
        whiteListed: $whitelist,
        omitNonBoarding: $omitNonBoarding,
        numberOfDepartures: $numberOfDepartures) {
      ...callData
    }
  }
"""
GRAPHQL_CALL_FRAGMENT = """
fragment callData on EstimatedCall {
  realtime
  aimedArrivalTime
  aimedDepartureTime
  expectedArrivalTime
  expectedDepartureTime
  destinationDisplay {
    frontText
  }
  serviceJourney {
    journeyPattern {
      line {
        id
        transportMode
        publicCode
      }
    }
  }
}
"""
GRAPHQL_DEPARTURE_CALLS_QUERY = f"""
query(
  $stops: [String],
  $quays: [String],
  $whitelist: InputWhiteListed,
  $numberOfDepartures: Int = 2,
  $omitNonBoarding: Boolean = true){{
    {GRAPHQL_STOP_TEMPLATE}
    {GRAPHQL_QUAY_TEMPLATE}
}}
{GRAPHQL_CALL_FRAGMENT}
"""
