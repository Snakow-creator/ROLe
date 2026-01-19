import Container from "../components/Container";

export default function Home() {
  return (
    <Container>
      <div className="container rounded-2xl mt-4 py-4 bg-white shadow-sm">
        <h1 className="text-3xl font-extrabold">Об игре</h1>

        <h4 className='text-xl mt-4 text-left xl:px-6 md:px-4 px-2'>
          Realme Of Life(ROLe) - это игра настоящий геймченджер в твоей жизни!<br></br>
          Начни же играть в ROLe сейчас же и получи роль самого легендарного геймченджера!
        </h4>
      </div>
    </Container>
  );
}
