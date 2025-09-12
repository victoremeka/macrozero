import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

function App() {
  const [count, setCount] = useState(0)

  return (
    <>
      <div>
        <a href="https://vite.dev" target="_blank">
          <img src={viteLogo} className="logo" alt="Vite logo" />
        </a>
        <a href="https://react.dev" target="_blank">
          <img src={reactLogo} className="logo react" alt="React logo" />
        </a>
      </div>
      <h1>Vite + React with shadcn/ui</h1>
      
      <Card className="w-[350px] mx-auto my-6">
        <CardHeader>
          <CardTitle>Counter Example</CardTitle>
          <CardDescription>Using shadcn/ui components</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-2xl font-bold text-center">Count: {count}</p>
        </CardContent>
        <CardFooter className="flex justify-between">
          <Button variant="outline" onClick={() => setCount((count) => count - 1)}>Decrease</Button>
          <Button onClick={() => setCount((count) => count + 1)}>Increase</Button>
        </CardFooter>
      </Card>
      
      <p className="read-the-docs">
        Click on the Vite and React logos to learn more
      </p>
    </>
  )
}

export default App
