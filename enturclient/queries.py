GRAPHQL_STOP_TO_QUAY_TEMPLATE = """
query(
    $stops: [String]!, 
    $omitNonBoarding: Boolean = true){
  stopPlaces(ids: $stops) {
    id
    quays(filterByInUse: true){
      id
      estimatedCalls(
          timeRange: 172100, 
          numberOfDepartures: 1,
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
        omitNonBoarding: $omitNonBoarding,
        numberOfDepartures: $numberOfDepartures) {
      realtime
      aimedArrivalTime
      aimedDepartureTime
      expectedArrivalTime
      expectedDepartureTime
      requestStop
      destinationDisplay {
        frontText
      }
      serviceJourney {
        journeyPattern {
          line {
            id
            name
            transportMode
            publicCode
          }
        }
      }
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
      realtime
      aimedArrivalTime
      aimedDepartureTime
      expectedArrivalTime
      expectedDepartureTime
      requestStop
      destinationDisplay {
        frontText
      }
      serviceJourney {
        journeyPattern {
          line {
            id
            name
            transportMode
            publicCode
          }
        }
      }
    }
  }
"""
