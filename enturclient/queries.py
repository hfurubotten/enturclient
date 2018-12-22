GRAPHQL_STOP_TO_QUAY_TEMPLATE = """{
  stopPlaces(ids: [$stops]) {
    id
    name
    latitude
    longitude
    quays{
      id
      name
      publicCode
      description
      latitude
      longitude
      estimatedCalls(
          startTime:\"$time\", 
          timeRange: 172100, 
          numberOfDepartures: 1){
        destinationDisplay {
          frontText
        }
      }
    }
  }
}
"""
GRAPHQL_STOP_TEMPLATE = """
  stopPlaces(ids: [$stops]) {
    id
    name
    estimatedCalls(
        $additionalOptions
        startTime: \"$time\",
        numberOfDepartures: 2) {
      realtime
      aimedArrivalTime
      aimedDepartureTime
      expectedArrivalTime
      expectedDepartureTime
      requestStop
      notices {
        text
      }
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
  quays(ids:[$quays]) {
    id
    name
    publicCode
    latitude
    longitude
    estimatedCalls(
        $additionalOptions
        startTime: \"$time\",
        numberOfDepartures: 2) {
      realtime
      aimedArrivalTime
      aimedDepartureTime
      expectedArrivalTime
      expectedDepartureTime
      requestStop
      notices {
        text
      }
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
